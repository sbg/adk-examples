import logging, json, datetime
from freyja import Automation, Step, Input, Output, List, Optional, Enum
from hephaestus import FindOrImportFiles, SetMetadataBulk, ExportFiles, SBApi
from hephaestus.types import File, VolumeFolder, Project
from app.context import Context
from app.types import Sample, Case, Cohort
from app.apps import BAMprep, WESsomatic, MultiQC


class Coverage(Enum):
    X30 = 30
    X40 = 40
    X50 = 50


class Main(Step):

    project_name = Input(
        str,
        name="Project name",
        description="Name of Seven Bridges project in which processing takes place. "
        "Re-uses existing project if found, otherwise creates new one.",
    )
    src_dir = Input(
        VolumeFolder,
        name="Input folder",
        description="Cloud bucket location containing input FASTq files.",
        default="external-demos/volumes_api_demo_bucket:tcrb",
    )
    dest_dir = Input(
        VolumeFolder,
        name="Output folder",
        description="Cloud bucket location for result files. "
        "Overwrites already existing files.",
        default="external-demos/volumes_api_demo_bucket:somatic-wes",
    )

    min_cov = Input(
        Optional[Coverage],
        name="Min. coverage",
        description="Minimum median read target coverage for BAM file to pass QC.",
        default=Coverage.X30,
    )

    project = Output(
        Project,
        name="Analysis project",
        description="SB project in which processing took place.",
    )
    report = Output(
        File,
        name="QC report",
        description="MultiQC report summarizing QC metrics (HTML format).",
    )
    pass_bams = Output(
        List[File], name="Pass BAM", description="BAM files that passed QC."
    )
    fail_bams = Output(
        List[File], name="Fail BAM", description="BAM files that failed QC."
    )
    vcfs = Output(
        List[File],
        name="Annotated MuTect VCFs",
        description="MuTect somatic variants calls for BAM fails that passed QC.",
    )

    def execute(self):
        "Execution starts here."

        # initialize context singleton used througout the automation
        Context().initialize(self.project_name)

        # import input FASTq files, set file metadata, and group by samples and cases
        cohort = ImportFilesAndGroupIntoCohort(src_dir=self.src_dir).cohort

        # processing
        self.prep_bams(cohort)
        self.call_somatic_variants(cohort)
        self.create_multiqc_report(cohort)

        # wrapping up
        self.export_results(cohort)
        self.collect_step_outputs(cohort)

    def prep_bams(self, cohort):
        "Runs BAMprep for each BAM file"

        for sample in cohort.samples:
            sample.bamprep = BAMprep(
                f"BAMprep-{sample.sample_id}",
                sample_id=sample.sample_id,
                fastq_files=sample.fastq_files,
            )

    def call_somatic_variants(self, cohort):
        "Calls somatic variants for each tumor/normal pair that passed QC"

        cohort.vcfs = []
        for case in cohort.cases:
            if self.passes_qc(case.tumor_sample) and self.passes_qc(
                case.normal_sample
            ):
                case.wes = WESsomatic(
                    f"WESsomatic-{case.case_id}",
                    case_id=case.case_id,
                    tumor_bam=case.tumor_sample.bamprep.output_bam,
                    normal_bam=case.normal_sample.bamprep.output_bam,
                )
                cohort.vcfs.append(case.wes.annotated_mutect_variants)

    def create_multiqc_report(self, cohort):
        "Runs MultiQC and get HTML report"

        multiqc_input_files = []
        for sample in cohort.samples:
            multiqc_input_files.extend(
                [
                    sample.bamprep.dedup_metrics,
                    sample.bamprep.recal_table,
                    sample.bamprep.alignment_metrics,
                    sample.bamprep.hs_metrics,
                ]
            )

        cohort.multi_qc_report = MultiQC(
            input_files=multiqc_input_files
        ).html_report

    def export_results(self, cohort):
        "Exports result files to connected cloud storage"

        bams = [s.bamprep.output_bam for s in cohort.samples]

        export_volume = SBApi().volumes.get(self.dest_dir.volume_id)
        ExportFiles(
            files=bams + cohort.vcfs,
            to_volume=export_volume,
            prefix=self.dest_dir.prefix,
            overwrite=True,
        )

    def collect_step_outputs(self, cohort):
        "Set values for all automation outputs to be shown on GUI"

        self.project = Context().project
        self.report = cohort.multi_qc_report
        self.pass_bams = [
            sample.bamprep.output_bam
            for sample in cohort.samples
            if self.passes_qc(sample)
        ]
        self.fail_bams = [
            sample.bamprep.output_bam
            for sample in cohort.samples
            if not self.passes_qc(sample)
        ]
        self.vcfs = cohort.vcfs

    def passes_qc(self, sample):
        "Returns true if sample passed QC."
        return sample.bamprep.median_target_coverage >= self.min_cov.value


class ImportFilesAndGroupIntoCohort(Step):
    """Finds FASTq files on volume, imports them into project, sets file 
    metadata, and returns cohort with files grouped by case and sample"""

    src_dir = Input(VolumeFolder)
    cohort = Output(Cohort)

    def execute(self):
        imported_files = self.import_files_from_volume()
        updated_files = self.update_file_metadata(imported_files)
        samples = self.group_files_by_sample(updated_files)
        cases = self.group_samples_by_case(samples)
        self.cohort = Cohort(cases=cases, name=self.src_dir.prefix)

    def import_files_from_volume(self):
        "Imports all fastq files found at volume source location"

        volume = SBApi().volumes.get(self.src_dir.volume_id)

        fastq_paths = [
            l.location
            for l in volume.list(prefix=self.src_dir.prefix)
            if l.location.endswith(".fastq")
        ]

        return FindOrImportFiles(
            filepaths=fastq_paths,
            from_volume=volume,
            to_project=Context().project,
        ).imported_files

    def update_file_metadata(self, files):
        """Sets file metadata in bulk for list of files based on file names.
        Setting metadata in bulk instead of per-file reduces API calls.
        Example filename: TCRBOA7-N-WEX-TEST.read1.fastq"""

        metadata = []
        for file in files:
            sample_id = file.name.split("-WEX")[0]
            paired_end = file.name.split("read")[1].split(".")[0]
            metadata.append({"sample_id": sample_id, "paired_end": paired_end})

        return SetMetadataBulk(to_files=files, metadata=metadata).updated_files

    def group_files_by_sample(self, files):
        """Groups files into list of sample objects for easier downstream
        processing."""

        samples = {}
        for file in files:
            sample_id = file.metadata["sample_id"]
            if sample_id not in samples:
                samples[sample_id] = Sample(sample_id)
            samples[sample_id].fastq_files.append(file)

        return list(samples.values())

    def group_samples_by_case(self, samples):
        cases = {}
        for sample in samples:
            (case_id, tissue) = sample.sample_id.split("-")
            if case_id not in cases:
                cases[case_id] = Case(case_id)
            if tissue == "T":
                cases[case_id].tumor_sample = sample
            elif tissue == "N":
                cases[case_id].normal_sample = sample
            else:
                raise Exception(f"Unknown tissue type: {tissue}")

        return list(cases.values())


if __name__ == "__main__":
    Automation(Main).run()
