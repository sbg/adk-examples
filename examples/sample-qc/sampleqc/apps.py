import datetime
import logging
from freyja import Input, Output, Step, List
from hephaestus import FindOrCreateAndRunTask, File, Task
from sampleqc.context import Context
from sampleqc.types import QCMetrics


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
            new_name=task_name + " - "
                + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            inputs=inputs,
            app=ctx.apps[app_name],
            in_project=ctx.project,
        ).finished_task


class BWAmem(AppStep):
    fastqs = Input(List[File])
    merged_bam = Output(File)

    def execute(self):
        ctx = Context()
        self.run_task(
            app_name="bwa",
            inputs={
                "FASTQ": self.fastqs, 
                "Input_reference": ctx.refs["bwa_bundle"]
            },
            task_name="BWAmem-" + self.fastqs[0].metadata["sample_id"],
        )

        self.merged_bam = self.task.outputs["merged_bam"]


class Trimgalore(AppStep):
    reads = Input(List[File])
    paired = Input(bool)
    fastqc = Input(bool)
    trimmed_reads = Output(List[File])

    def execute(self):
        self.run_task(
            app_name="trimgalore",
            inputs={
                "reads": self.reads, 
                "paired": self.paired, 
                "fastqc": self.fastqc
            },
            task_name="Trimgalore-" + self.reads[0].metadata["sample_id"],
        )

        self.trimmed_reads = self.task.outputs["trimmed_reads"]


class PicardAlignmentSummaryMetrics(AppStep):
    input_bam = Input(File)

    summary_metrics_file = Output(File)
    qc_metrics = Output(QCMetrics)

    def execute(self):
        ctx = Context()
        self.run_task(
            app_name="alignmentqc",
            inputs={
                "input_bam": self.input_bam,
                "reference": ctx.refs["reference_fasta"],
            },
            task_name="AlignmentQC-" + self.input_bam.metadata["sample_id"],
        )

        self.summary_metrics_file = self.task.outputs["summary_metrics"]
        self.qc_metrics = self.parse_qc_from_metrics_file()

        logging.info(f"pct_pf_reads_aligned: {self.qc_metrics.pct_pf_reads_aligned}")
        logging.info(f"strand balance: {self.qc_metrics.strand_balance}")

    def parse_qc_from_metrics_file(self):
        "reads QC metrics from picard output file into QC object"

        for s in self.summary_metrics_file.stream():
            for line in s.decode("utf-8").split("\n"):
                if not line.startswith("PAIR"):
                    continue
                record = line.strip().split("\t")

                return QCMetrics(
                    bam_file=self.input_bam,
                    pct_pf_reads_aligned=float(record[6]),
                    strand_balance=float(record[19]),
                )


class PicardMarkDuplicates(AppStep):
    input_bam = Input(File)
    deduped_bam = Output(File)

    def execute(self):
        self.run_task(
            app_name="markdup",
            inputs={
                "input_bam": [self.input_bam]
            },
            task_name="MarkDup-" + self.input_bam.metadata["sample_id"],
        )

        self.deduped_bam = self.task.outputs["deduped_bam"]
