import logging, tempfile
from freyja import Automation, Step, Input, List, Output, Optional
from hephaestus import File, UploadFile
from sampleqc.manifest import load_manifest
from sampleqc.context import Context
from sampleqc.apps import BWAmem, Trimgalore, \
    PicardAlignmentSummaryMetrics, PicardMarkDuplicates         
    
class Main(Step):
    '''From multi-lane FASTQ files to merged duplicate-marked BAMs,
    with conditional execution depending on QC metrics.
    
    To run locally, change into project directory and type:
    
    $ python -m sampleqc run --manifest_filename manifest.tsv --project_name my_project
    '''
    
    manifest_filename = Input(str)
    project_name = Input(str)
    qc_summary = Output(File)

    def execute(self):
        'Main execution method. Execution starts here.'
        
        # setup execution project, stage apps, ref files
        Context().initialize(project_name=self.project_name)
        
        # parse manifest into cohort, import fastq files, set metadata
        cohort = load_manifest(self.manifest_filename)

        for sample in cohort.samples:

            # run trimgalore on all lanes
            trimgalore = Trimgalore(f"Trimgalore-{sample.id}",
                reads=sample.fastqs,
                paired=True,
                fastqc=True
            )

            # only keep fastq pairs that meet quality cutoff
            filterfastq = FilterFastq(f"FilterFastq-{sample.id}", 
                input_fastq=trimgalore.trimmed_reads
            )

            # run BWA on remaining lanes
            bwa = BWAmem(f"BWAmem-{sample.id}",
                fastqs=filterfastq.pass_fastq
            )

            # process BAM conditioned on alignment QC
            sample.processbam = ProcessBam(f"ProcessBam-{sample.id}",
                input_bam = bwa.merged_bam,
                sample_id = sample.id
            )
            
        # upload QC metrics summary and return on output
        self.qc_summary = self.upload_qc_metrics(cohort)
        

    def upload_qc_metrics(self, cohort):
        '''Collects BAM QC metrics from all processed samples and uploads
        summary file in tab-separated format to SB project. Overwrites 
        existing file. Returns uploaded file object.'''
        
        # note: don't create a transient temporary file (not thread safe) 
        temp_filename = tempfile.gettempdir() + "/bam_qc_metrics.tsv"
        temp = open(temp_filename, "wt")
            
        # write header
        temp.write("\t".join([
            "sample_id", 
            "bam_file", 
            "pct_pf_reads_aligned", 
            "strand_balance",
            "status"]) + "\n")
        
        # write content
        for sample in cohort.samples:
            bam_step = sample.processbam
            temp.write("\t".join([
                sample.id,
                bam_step.input_bam.name,
                str(bam_step.qc_metrics['pct_pf_reads_aligned']),
                str(bam_step.qc_metrics['strand_balance']),
                bam_step.qc_metrics['status']]) + "\n") 
        temp.close()
        
        # upload file to platform (overwrites existing file)
        return UploadFile("UploadMetrics",
            local_path=temp.name, 
            to_project=Context().project, 
            overwrite=True).file

        
class FilterFastq(Step):
    'Filters out FASTq files not meeting QC criteria'
    
    input_fastq = Input(List[File])
    pass_fastq = Output(List[File])

    def execute(self):
        self.pass_fastq = [
            fq for fq in self.input_fastq 
            if fq.size > self.config_.qc.min_fastq_size
        ]


class ProcessBam(Step):
    '''Performs alignment QC and duplicate marking 
    for single sample'''
    
    input_bam = Input(File)
    sample_id = Input(str)
    processed_bam = Output(Optional[File])
    qc_metrics = Output(dict)

    def execute(self):

        # compute alignment quality metrics
        alignment_qc = PicardAlignmentSummaryMetrics(
            f"AlignmentSummaryMetrics-{self.sample_id}",
            input_bam=self.input_bam 
        )
        
        # if BAM failed QC, we are done here (dynamic conditional)
        # thread block here until QC metrics finished computing
        if alignment_qc.metrics_ok():

            # mark duplicates if required (static conditional)
            if self.config_.skip_duplicate_marking:
                self.processed_bam = self.input_bam
            else:
                self.processed_bam = PicardMarkDuplicates(
                    f"MarkDuplicates-{self.sample_id}",
                    input_bam=self.input_bam
                ).deduped_bam
        else:
            logging.info(f"Sample failed QC: {self.input_bam.name}")
            self.processed_bam = None

        self.qc_metrics = { 
            'pct_pf_reads_aligned' : float(alignment_qc.pct_pf_reads_aligned),
            'strand_balance' : float(alignment_qc.strand_balance),
            'status' : "PASS" if alignment_qc.metrics_ok() else "FAIL"
        }

                

if __name__ == '__main__':
    Automation(Main).run()
