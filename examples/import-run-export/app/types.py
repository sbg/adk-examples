from freyja import Type, List
from hephaestus import File


class Sample(Type):
    """Custom type representing sample with input files. Use as an example 
    to see how to create custom types that can be used as step inputs and 
    outputs. Custom types must implement a serialize and deserialize method."""

    def __init__(self, sample_id, fastq_files=None):
        self.sample_id = sample_id
        self.fastq_files = fastq_files or []

    @classmethod
    def init(cls, val):
        pass
    
    @classmethod
    def _serialize(cls, val):
        return {
            "sample_id": val.sample_id,
            "fastq_files": List[File]._serialize(val.fastq_files),
        }

    @classmethod
    def _deserialize(cls, val):
        return Sample(
            sample_id = val["sample_id"],
            fastq_files = List[File]._deserialize(val["fastq_files"])
        )

