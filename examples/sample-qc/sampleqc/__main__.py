import logging
from freyja import Automation, Step, Input, List, Output, Optional
from hephaestus import File, Project
from sampleqc.manifest import load_manifest
from sampleqc.context import Context
from sampleqc.steps import CollectAndUploadQCSummary
from sampleqc.types import BamQCMetrics, ProcessedBam
from sampleqc.utils import bam_qc_metrics_ok
from sampleqc.apps import (
    BWAmem,
    Trimgalore,
    PicardAlignmentSummaryMetrics,
    PicardMarkDuplicates,
)


class Main(Step):
    """From multi-lane FASTQ files to merged duplicate-marked BAMs,
    with conditional execution depending on QC metrics.
    
    To run locally, change into project directory and type:
    
    $ python -m sampleqc run --project_name <sb_project_name> [--manifest_file <sb_file_id>]
    
    whereas <sb_project_name> refers to name of a SB project within which processing
    will take place, and <sb_file_id> is the file ID of the manifest file stored on 
    the SB platform. If a project with specified name is found, it re-uses this project
    and all the analysis results already in this project (memoization). Otherwise,
    a new project with that name is created.
    """

    manifest_file = Input(
        File, 
        name="Manifest file", 
        description="Tab-seperated file listing samples and files to be processed.",
        default="5c9bb5c3e4b09d72204aac44"
    )
    project_name = Input(
        str,
        name="Project name",
        description="Name of platform project. Re-uses existing project if found, otherwise create new one.",
    )

    project = Output(
        Project,
        name="Analysis project",
        description="SB project in which processing took place.",
    )
    qc_summary = Output(
        File,
        name="QC summary",
        description="Tab-separated file containing collected QC metrics."
    )

    def execute(self):
        "Main execution method. Execution starts here."

        # setup execution project, stage apps, ref files
        Context().initialize(project_name=self.project_name)

        # parse manifest into cohort, import fastq files, set metadata
        cohort = load_manifest(self.manifest_file)

        # process samples in loop 
        # note: processing happens in parallel due to use of promises
        processed_bams = [
            ProcessSample(fastqs=s.fastqs, name_=s.id).processed_bam
            for s in cohort.samples
        ]

        # collect BAM QC metrics and upload summary file
        self.qc_summary = CollectAndUploadQCSummary(
            processed_bams=processed_bams
        ).uploaded_file
        
        # provide analysis project on output
        self.project = Context().project


class ProcessSample(Step):
    "Processes a single sample"

    fastqs = Input(List[File])
    processed_bam = Output(ProcessedBam)

    def execute(self):
        tg = Trimgalore(reads=self.fastqs, paired=True, fastqc=True)
        filter = FilterFastq(input_fastq=tg.trimmed_reads)
        aligned_bam = BWAmem(fastqs=filter.pass_fastq).merged_bam
        self.processed_bam = ProcessBam(input_bam=aligned_bam).processed_bam


class FilterFastq(Step):
    "Filters out FASTq files not meeting QC criteria"

    input_fastq = Input(List[File])
    pass_fastq = Output(List[File])

    def execute(self):
        self.pass_fastq = [
            fq for fq in self.input_fastq
            if fq.size > self.config_.qc.min_fastq_size
        ]


class ProcessBam(Step):
    """Processes single BAM file including alignment QC.
    If mark duplicates is not required (static conditional) or
    BAM failed alignment QC (dynamic conditional), returns input BAM
    without further processing. Otherwise, runs deduplication and
    return deduplicated BAM"""
        
    input_bam = Input(File)
    processed_bam = Output(ProcessedBam)

    def execute(self):

        asm = PicardAlignmentSummaryMetrics(input_bam=self.input_bam)
        qc_failed = not bam_qc_metrics_ok(asm.qc_metrics, self.config_)

        if self.config_.skip_duplicate_marking or qc_failed:
            self.processed_bam = ProcessedBam(self.input_bam, asm.qc_metrics)
        else:
            md = PicardMarkDuplicates(input_bam=self.input_bam)
            self.processed_bam = ProcessedBam(md.deduped_bam, asm.qc_metrics)


if __name__ == "__main__":
    Automation(Main).run()
