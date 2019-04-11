import logging
from freyja import Automation, Step, Input, List, Output, Optional
from hephaestus import File
from sampleqc.manifest import load_manifest
from sampleqc.context import Context
from sampleqc.steps import CollectAndUploadQCSummary
from sampleqc.types import QCMetrics
from sampleqc.utils import bam_qc_metrics_ok
from sampleqc.apps import (
    BWAmem,
    Trimgalore,
    PicardAlignmentSummaryMetrics,
    PicardMarkDuplicates
)


class Main(Step):
    """From multi-lane FASTQ files to merged duplicate-marked BAMs,
    with conditional execution depending on QC metrics.
    
    To run locally, change into project directory and type:
    
    $ python -m sampleqc run --manifest_filename manifest.tsv --project_name my_project
    """

    manifest_filename = Input(str)
    project_name = Input(str)
    qc_summary = Output(File)

    def execute(self):
        "Main execution method. Execution starts here."

        # setup execution project, stage apps, ref files
        Context().initialize(project_name=self.project_name)

        # parse manifest into cohort, import fastq files, set metadata
        cohort = load_manifest(self.manifest_filename)

        for sample in cohort.samples:

            # process sample in seprate step
            # step must be named explicitly b/c of loop
            ps = ProcessSample(f"Process-{sample.id}", fastqs=sample.fastqs)

            # collect results for downstream aggregation steps
            sample.aligned_bam = ps.aligned_bam
            sample.bam_qc_metrics = ps.bam_qc_metrics

        # upload QC metrics summary file to SB platform and 
        # provide uploaded file on output
        self.qc_summary = CollectAndUploadQCSummary(
            qc_metrics=[s.bam_qc_metrics for s in cohort.samples]
        ).uploaded_file


class ProcessSample(Step):
    "Processes a single sample"

    fastqs = Input(List[File])
    aligned_bam = Output(File)
    processed_bam = Output(File)
    bam_qc_metrics = Output(QCMetrics)

    def execute(self):

        # run trimgalore on all lanes
        tg = Trimgalore(reads=self.fastqs, paired=True, fastqc=True)

        # only keep fastq pairs that meet quality cutoff
        filter = FilterFastq(input_fastq=tg.trimmed_reads)

        # run BWA on remaining lanes and provide BAM on output;
        # immediately unblocks other steps waiting for BAM output,
        # even before this execute() function finishes
        self.aligned_bam = BWAmem(fastqs=filter.pass_fastq).merged_bam

        # process BAM with conditional execution inside
        process_bam = ProcessBam(input_bam=self.aligned_bam)

        # return processed BAM and BAM QC metrics as output
        self.processed_bam = process_bam.processed_bam
        self.bam_qc_metrics = process_bam.qc_metrics


class FilterFastq(Step):
    "Filters out FASTq files not meeting QC criteria"

    input_fastq = Input(List[File])
    pass_fastq = Output(List[File])

    def execute(self):
        self.pass_fastq = [
            fq for fq in self.input_fastq if fq.size > self.config_.qc.min_fastq_size
        ]


class ProcessBam(Step):
    """Processes single BAM file with execution conditioned on
    automation setting (static conditional) and alignment QC
    metric (dynamic conditional)."""

    input_bam = Input(File)
    processed_bam = Output(File)
    qc_metrics = Output(QCMetrics)

    def execute(self):

        # compute alignment quality metrics and provide on output
        picard = PicardAlignmentSummaryMetrics(input_bam=self.input_bam)
        self.qc_metrics = picard.qc_metrics

        # if mark duplicates is not required return input BAM;
        # note: static conditional that does not cause exeuction block
        if self.config_.skip_duplicate_marking:
            self.processed_bam = self.input_bam
            return

        # if BAM failed QC do not process further and return input BAM;
        # note: dynamic conditional that blocks this thread until QC
        # metrics finished computing
        if not bam_qc_metrics_ok(self.qc_metrics, self.config_):
            logging.info(f"Sample failed QC: {self.input_bam.name}")
            self.processed_bam = self.input_bam
            return

        # mark duplicates and return de-duped BAM as result
        self.processed_bam = PicardMarkDuplicates(input_bam=self.input_bam).deduped_bam


if __name__ == "__main__":
    Automation(Main).run()
