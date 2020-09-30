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
            sample_id=val["sample_id"],
            fastq_files=List[File]._deserialize(val["fastq_files"]),
        )


class Case(Type):
    """Custom type representing tumor/normal pair of samples"""

    def __init__(self, case_id, tumor_sample=None, normal_sample=None):
        self.case_id = case_id
        self.tumor_sample = tumor_sample
        self.normal_sample = normal_sample

    @classmethod
    def init(cls, val):
        pass

    @classmethod
    def _serialize(cls, val):
        return {
            "case_id": val.case_id,
            "tumor_sample": Sample._serialize(val.tumor_sample),
            "normal_sample": Sample._serialize(val.normal_sample),
        }

    @classmethod
    def _deserialize(cls, val):
        return Case(
            case_id=val["case_id"],
            tumor_sample=Sample._deserialize(val["tumor_sample"]),
            normal_sample=Sample._deserialize(val["normal_sample"]),
        )

    @property
    def samples(self):
        yield self.tumor_sample
        yield self.normal_sample


class Cohort(Type):
    """Custom type representing a set of cases"""

    def __init__(self, cases, name=None):
        self.cases = cases
        self.name = name

    @classmethod
    def init(cls, val):
        pass

    @classmethod
    def _serialize(cls, val):
        return {"name": val.name, "cases": List[Case]._serialize(val.cases)}

    @classmethod
    def _deserialize(cls, val):
        return Cohort(
            cases=List[Case]._deserialize(val["cases"]), name=val["name"]
        )

    @property
    def samples(self):
        for case in self.cases:
            for sample in case.samples:
                yield sample
