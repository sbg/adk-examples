class Cohort:
    "set of patients to be analyzed"

    def __init__(self, manifest_file):
        "load patient and sample data from manifest file"

        self.manifest_file = manifest_file
        self.patients = []

    def get_sample_by_id(self, id):
        sample = [s for p in self.patients for s in p.samples if s.id == id]
        return sample[0] if sample else None

    def get_patient_by_id(self, id):
        patient = [p for p in self.patients if p.id == id]
        return patient[0] if patient else None

    def add_patient(self, patient):
        if self.get_patient_by_id(patient.id):
            raise Exception("Cohort already has patient with ID %s" % patient.id)
        self.patients.append(patient)
        patient.cohort = self

    @property
    def samples(self):
        for p in self.patients:
            for s in p.samples:
                yield s

    @property
    def normal_samples(self):
        for s in self.samples:
            if s.source in ["normal", "blood"]:
                yield s

    def __repr__(self):
        return "<Cohort: manifest_file=%s patients=%s>" % (
            self.manifest_file,
            self.patients,
        )


class Patient:
    """patient with samples, as parsed from manifest."""

    def __init__(self, id):
        self.id = id
        self.samples = []
        self.cohort = None

    def get_sample_by_id(self, id):
        sample = [s for s in self.samples if s.id == id]
        return sample[0] if sample else None

    def add_sample(self, sample):
        if self.get_sample_by_id(sample.id):
            raise Exception(
                "Patient %s already has sample with ID %s" % (self.id, sample.id)
            )
        self.samples.append(sample)
        sample.patient = self

    def __repr__(self):
        return "<Patient: id=%s samples=%s>" % (self.id, self.samples)


class Sample:
    """sample with associated sequencing files, as parsed from manifest. 
    this class also holds all analysis results for a sample."""

    def __init__(self, id, type=None, source=None):
        self.id = id
        self.type = type  # tumor type
        self.source = source  # tumor or normal
        self.lanes = []
        self.patient = None

    def add_lane(self, lane):
        self.lanes.append(lane)
        lane.sample = self

    @property
    def multilane(self):
        return len(self.lanes) > 1

    @property
    def fastqs(self):
        fqs = []
        for l in self.lanes:
            fqs.extend([l.fq1, l.fq2])
        return fqs

    def __repr__(self):
        return "<Sample: id=%s type=%s source=%s lane=%s patient=%s>" % (
            self.id,
            self.type,
            self.source,
            self.lanes,
            self.patient.id if self.patient else None,
        )


class Lane:
    """pair of fastq files with origin information. a sample can consist of multiple lanes."""

    def __init__(
        self,
        read_group=1,
        fq1=None,
        fq2=None,
        file_name_root=None,
        library_name=None,
        processing_unit=None,
    ):
        self.read_group = int(read_group)
        self.fq1 = fq1
        self.fq2 = fq2
        self.file_name_root = file_name_root
        self.library_name = library_name
        self.processing_unit = processing_unit
        self.sample = None

    @property
    def id(self):
        id = self.sample.id
        if self.sample.multilane:
            id += ": " + str(self.read_group)
        return id

    def __repr__(self):
        return "<Lane: read_group=%s fq1=%s fq2=%s FN=%s LB=%s PU=%s sample=%s>" % (
            self.read_group,
            self.fq1,
            self.fq2,
            self.file_name_root,
            self.library_name,
            self.processing_unit,
            self.sample.id if self.sample else None,
        )
