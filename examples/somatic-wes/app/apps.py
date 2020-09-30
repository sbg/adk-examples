import datetime
import logging
from freyja import Input, Output, Step, List, Optional
from hephaestus import FindOrCreateAndRunTask, File, Task
from app.context import Context


class AppStep(Step):
    """Base class for all steps executing apps on the SB platform.
    Finished task is return on 'task' output."""

    task = Output(Task)

    def run_task(self, app_name, inputs, task_name=None):
        """Executes app on SB platform and returns finished task.
        'app_name' must have defined app in automation config file."""

        ctx = Context()
        if not task_name:
            task_name = self.name_

        self.task = FindOrCreateAndRunTask(
            new_name=task_name
            + " - "
            + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            inputs=inputs,
            app=ctx.apps[app_name],
            in_project=ctx.project,
        ).finished_task


class BAMprep(AppStep):
    sample_id = Input(str)
    fastq_files = Input(List[File])

    dedup_metrics = Output(File)
    recal_table = Output(File)
    alignment_metrics = Output(File)
    hs_metrics = Output(File)
    per_target_coverage = Output(File)
    output_bam = Output(File)
    median_target_coverage = Output(int)

    def execute(self):
        ctx = Context()
        self.run_task(
            app_name="bam_prep",
            inputs={
                "input_reads": self.fastq_files,
                "input_tar_with_reference": ctx.refs["hg19_fasta"],
                "bait_bed": ctx.refs["sureselect_xt"],
                "target_bed": ctx.refs["v5_core"],
                "kgsnp_database": ctx.refs["g1k_snps"],
                "mgindel_database": ctx.refs["hc_indels"],
            },
            task_name="BAMprep-" + self.sample_id,
        )

        self.dedup_metrics = self.task.outputs["dedup_metrics"]
        self.recal_table = self.task.outputs["recal_table"]
        self.alignment_metrics = self.task.outputs["alignment_metrics"]
        self.hs_metrics = self.task.outputs["hs_metrics"]
        self.per_target_coverage = self.task.outputs["per_target_coverage"]
        self.output_bam = self.task.outputs["output_bam"]
        self.hs_metrics = self.task.outputs["hs_metrics"]
        self.median_target_coverage = self.get_median_target_coverage(
            self.hs_metrics
        )

    def get_median_target_coverage(self, file):
        "Parses median target coverage from hs metrics file"

        for line in file.content().split("\n"):
            if line.startswith("SureSelect"):
                return int(line.strip().split("\t")[23])


class WESsomatic(AppStep):
    case_id = Input(str)
    tumor_bam = Input(File)
    normal_bam = Input(File)

    annotated_mutect_variants = Output(File)

    def execute(self):
        ctx = Context()
        self.run_task(
            app_name="wes_somatic",
            inputs={
                "tumor_reads": self.tumor_bam,
                "normal_reads": self.normal_bam,
                "target_bed": ctx.refs["v5_core"],
                "kgsnp_database": ctx.refs["g1k_snps"],
                "kgindel_database": ctx.refs["g1k_indels"],
                "mgindel_database": ctx.refs["hc_indels"],
                "snpEff_database": ctx.refs["snpeff"],
                "cosmic_database": ctx.refs["cosmic"],
                "cache_file": ctx.refs["vep"],
                "annotation_reference": ctx.refs["grch37_fasta"],
                "ExAC_database": ctx.refs["exac"],
                "input_tar_with_reference": ctx.refs["hg19_fasta"],
                "dbSNP": ctx.refs["dbsnp_138"],
            },
            task_name="WESsomatic-" + self.case_id,
        )

        self.annotated_mutect_variants = self.task.outputs[
            "annotated_mutect_variants"
        ]


class MultiQC(AppStep):
    input_files = Input(List[File])
    config_files = Input(Optional[List[File]])
    sample_names = Input(Optional[File])

    html_report = Output(File)
    pdf_report = Output(File)

    def execute(self):
        ctx = Context()
        self.run_task(
            app_name="multi_qc",
            inputs={
                "in_reports": self.input_files,
                "config": self.config_files,
                "sample_names": self.sample_names,
                "pdf": True,
            },
            task_name="MultiQC",
        )

        self.html_report = self.task.outputs["out_html"]
        self.pdf_report = self.task.outputs["out_pdf"]
