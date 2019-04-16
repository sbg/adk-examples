"""
Custom types that can be used for step inputs and outputs. 
Use as template to create your own custom types. Custom types 
must implement a serialize and deserialize method.
"""

from freyja import Type
from hephaestus import File


class BamQCMetrics(Type):

    def __init__(self, pct_pf_reads_aligned, strand_balance):
        self.pct_pf_reads_aligned = pct_pf_reads_aligned
        self.strand_balance = strand_balance

    @classmethod
    def init(cls, val):
        pass
    
    @classmethod
    def _serialize(cls, val):
        return {
            "pct_pf_reads_aligned": val.pct_pf_reads_aligned,
            "strand_balance": val.strand_balance
        }

    @classmethod
    def _deserialize(cls, val):
        return BamQCMetrics(
            pct_pf_reads_aligned=float(val["pct_pf_reads_aligned"]), 
            strand_balance=float(val["strand_balance"])
        )

class ProcessedBam(Type):

    def __init__(self, bam_file, qc_metrics=None):
        self.bam_file = bam_file
        self.qc_metrics = qc_metrics

    @classmethod
    def init(cls, val):
        pass
    
    @classmethod
    def _serialize(cls, val):
        return {
            "bam_file": File._serialize(val.bam_file),
            "qc_metrics": BamQCMetrics._serialize(val.qc_metrics)
        }

    @classmethod
    def _deserialize(cls, val):
        return ProcessedBam(
            bam_file=File._deserialize(val["bam_file"]), 
            qc_metrics=BamQCMetrics._deserialize(val["qc_metrics"])
        )
    