import logging, json, datetime
from freyja import Automation, Step, Input, Output, List, Optional
from hephaestus import (
    FindOrImportFiles,
    SetMetadataBulk,
    ExportFiles,
    FindOrCreateAndRunTask,
)
from hephaestus.types import File, VolumeFolder, Project
from hephaestus.steps import SBApi
from app.context import Context
from app.types import Sample


class Main(Step):
    """Imports FASTq files from a cloud bucket, aligns them with BWA, and exports 
    resulting BAM files back to a cloud bucket location. 
    
    To run this automation from your local computer, type the following command
    while inside the project root directory:
    
      python -m app run --project_name <project-name> [--src_dir <location>] [--dest_dir <location>]
      
    whereas <location> refers to a cloud bucket directory in format <sb-volume-id>:<bucket-prefix>.
    If not provided, location defaults as specified in the automation code are used.
    
    """

    project_name = Input(
        str,
        name="Project name",
        description="Name of platform project. Re-uses existing project if found, otherwise create new one.",
    )
    src_dir = Input(
        VolumeFolder,
        name="Input folder",
        description="Cloud bucket location containing input FASTq files.",
        default="external-demos/volumes_api_demo_bucket:inputs",
    )
    dest_dir = Input(
        VolumeFolder,
        name="Output folder",
        description="Cloud bucket location for result files. Overwrites already existing files.",
        default="external-demos/volumes_api_demo_bucket:automation/import-run-export/result",
    )

    project = Output(
        Project,
        name="Analysis project",
        description="SB project in which processing took place.",
    )
    bams = Output(
        List[File],
        name="BAM files",
        description="BAM files containing aligned reads.",
    )

    def execute(self):
        "Execution starts here."

        # initialize context singleton used througout the automation
        ctx = Context().initialize(self.project_name)

        # stage input FASTq files, set file metadata, and group by samples
        samples = ImportFilesAndGroupBySample(src_dir=self.src_dir).samples

        # run BWA for each sample; samples are processed in parallel
        # because app outputs are promises and we can use them
        # before results are available (lazy evaluation)
        self.bams = [
            BWAmem(
                f"BWAmem-{sample.sample_id}",  # name the step (must be unique)
                input_reads=sample.fastq_files
            ).aligned_reads
            for sample in samples
        ]

        # export all BAM files to volume; export step starts executing
        # as soon as all BAM files have become available
        export_volume = SBApi().volumes.get(self.dest_dir.volume_id)
        ExportFiles(
            files=self.bams,
            to_volume=export_volume,
            prefix=self.dest_dir.prefix,
            overwrite=True,
        )

        # capture analysis project as output
        self.project = ctx.project


class ImportFilesAndGroupBySample(Step):
    """Finds FASTq files on volume, imports them into project, sets file 
    metadata, and returns updated files grouped by sample"""

    src_dir = Input(VolumeFolder)
    samples = Output(List[Sample])

    def execute(self):
        imported_files = self.import_files_from_volume()
        updated_files = self.update_file_metadata(imported_files)
        self.samples = self.group_files_by_sample(updated_files)

    def import_files_from_volume(self):
        "Imports all fastq files found at volume source location"

        volume = SBApi().volumes.get(self.src_dir.volume_id)

        fastq_paths = [
            l.location
            for l in volume.list(prefix=self.src_dir.prefix)
            if "TCRBOA7" in l.location and l.location.endswith(".fastq")
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


class BWAmem(Step):
    """Wrapper step that runs BWA-MEM on SB platform and provides task
    outputs as named step outputs."""

    input_reads = Input(List[File])
    aligned_reads = Output(File)

    def execute(self):
        ctx = Context()
        task = FindOrCreateAndRunTask(
            inputs={
                "input_reads": self.input_reads,
                "reference_index_tar": ctx.refs["bwa_bundle"],
            },
            new_name="BWAmem - "  # name task after sample ID
            + self.input_reads[0].metadata["sample_id"]
            + " - "
            + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            app=ctx.apps["bwa"],
            in_project=ctx.project,
        ).finished_task

        self.aligned_reads = task.outputs["aligned_reads"]


if __name__ == "__main__":
    Automation(Main).run()
