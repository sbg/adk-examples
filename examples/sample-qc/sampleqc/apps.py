import datetime
import logging
from freyja import Input, Output, Step, List
from hephaestus import FindOrCreateAndRunTask, File
from sampleqc.context import Context

class AppStep(Step):     
    
    def execute_app(self, app_name, inputs):
        'executes app on SB platform and returns finished task'
        
        ctx = Context()    
        task = FindOrCreateAndRunTask(f"FindOrCreateAndRunTask-{self.name_}",
            new_name = self.name_ + " - " + 
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            inputs=inputs,
            app=ctx.apps[app_name],
            in_project=ctx.project
        ).finished_task
    
        return task

class BWAmem(AppStep):
    fastqs = Input(List[File])
    merged_bam = Output(File)
        
    def execute(self):
        ctx = Context()    
        task = self.execute_app("bwa",
            inputs = {
                'FASTQ' : self.fastqs,
                'Input_reference' : ctx.refs["bwa_bundle"]
            })
        
        self.merged_bam = task.outputs['merged_bam']

class Trimgalore(AppStep):
    reads = Input(List[File])
    paired = Input(bool)
    fastqc = Input(bool)
    trimmed_reads = Output(List[File])
        
    def execute(self):
        task = self.execute_app("trimgalore", 
            inputs = {
                'reads' : self.reads,
                'paired' : self.paired,
                'fastqc' : self.fastqc
            })
        
        self.trimmed_reads = task.outputs['trimmed_reads']

class PicardAlignmentSummaryMetrics(AppStep):
    input_bam = Input(File)

    summary_metrics = Output(File)
    pct_pf_reads_aligned = Output(float)
    strand_balance = Output(float)
    
    def execute(self):
        ctx = Context()
        task = self.execute_app("alignmentqc", 
            inputs = {
                'input_bam' : self.input_bam,
                'reference' : ctx.refs["reference_fasta"]
            })

        self.summary_metrics = task.outputs['summary_metrics']
        self.parse_qc_from_metrics_file()

    def parse_qc_from_metrics_file(self):
        for s in self.summary_metrics.stream():
            for line in s.decode("utf-8").split("\n"):
                if not line.startswith("PAIR"):
                    continue
    
                record = line.strip().split("\t")
                self.pct_pf_reads_aligned = float(record[6])
                self.strand_balance = float(record[19])
                break

        logging.info(f"Total pct_pf_reads_aligned: {self.pct_pf_reads_aligned}")
        logging.info(f"Total strand balance: {self.strand_balance}")
        
    def metrics_ok(self):
        return self.pct_pf_reads_aligned \
                    >= self.config_.qc.min_pct_pf_reads_aligned and \
               abs(self.strand_balance) \
                    >= self.config_.qc.min_strand_balance            


class PicardMarkDuplicates(AppStep):
    input_bam = Input(File)
    deduped_bam = Output(File)
    
    def execute(self):
        task = self.execute_app("markdup", 
            inputs = {
                'input_bam' : [self.input_bam]
            })
        
        self.deduped_bam = task.outputs['deduped_bam']

