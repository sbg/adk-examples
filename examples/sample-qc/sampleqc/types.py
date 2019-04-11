from freyja import Type
from hephaestus import File


class QCMetrics(Type):
    """Custom type to store QC metrics for given BAM file. Use this
    as an example to see how to create custom types that can be used
    as step inputs and outputs. Custom types must implement a serialize 
    and deserialize method."""

    def __init__(self, bam_file, pct_pf_reads_aligned, strand_balance):
        self.bam_file = bam_file
        self.pct_pf_reads_aligned = pct_pf_reads_aligned
        self.strand_balance = strand_balance

    @classmethod
    def _serialize(cls, val):
        return {
            "bam_file": File._serialize(val.bam_file),
            "pct_pf_reads_aligned": val.pct_pf_reads_aligned,
            "strand_balance": val.strand_balance,
        }

    @classmethod
    def _deserialize(cls, val):
        val.bam_file = File._deserialize(val["bam_file"])
        val.pct_pf_reads_aligned = float(val["pct_pf_reads_aligned"])
        val.strand_balance = float(val["strand_balance"])
