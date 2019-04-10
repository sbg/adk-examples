import os, tempfile
import logging
from hephaestus.steps import FindOrCopyFilesByName, SBApi, SetMetadataBulk
from sampleqc.context import Context
from sampleqc.entities import Cohort, Patient, Sample, Lane


def load_manifest(filename):
    "Parses given manifest file into cohort object structure"

    def load(filename):

        cohort = parse_manifest_into_cohort(filename)
        stage_input_files_in_bulk(cohort)
        set_metadata_in_bulk(cohort)

        return cohort

    def parse_manifest_into_cohort(filename):

        logging.info(f"Reading manifest file: '{filename}'")

        if filename.startswith("sb://"):
            project_id, file_name = os.path.split(filename[5:])
            sbfile = FindOrCopyFilesByName(
                f"CopyManifest",
                names=[file_name],
                from_project=SBApi().projects.get(project_id),
                to_project=Context().project,
            ).copied_files[0]
            filename = tempfile.gettempdir() + "/manifest.txt"
            sbfile.download(path=filename)

        cohort = Cohort(manifest_file=filename)

        num_entries = 0
        with open(str(filename), "r") as f:
            for line_no, line in enumerate(f.readlines()):

                if line_no == 0:  # skip header
                    continue

                if line.strip().startswith("#"):
                    continue

                patient_id, sample_id, read_group, fq1, fq2 = line.strip().split("\t")

                patient = cohort.get_patient_by_id(patient_id)
                if not patient:
                    patient = Patient(patient_id)
                    cohort.add_patient(patient)

                sample = patient.get_sample_by_id(sample_id)
                if not sample:
                    sample = Sample(sample_id)
                    patient.add_sample(sample)

                lane = Lane(read_group=read_group, fq1=fq1, fq2=fq2)
                sample.add_lane(lane)

                num_entries += 1

        logging.info(
            "  %d manifest entries read." % num_entries
        )  # will equals total number of samples * number of lanes

        return cohort

    def stage_input_files_in_bulk(cohort):
        "Copy all input files to execution project in bulk to save API calls"

        ctx = Context()

        fastq_project = SBApi().projects.get(id=ctx.config.fastq_project)

        files_to_stage = [
            f for s in cohort.samples for l in s.lanes for f in [l.fq1, l.fq2]
        ]

        staged_files = FindOrCopyFilesByName(
            "StageInputs",
            names=files_to_stage,
            from_project=fastq_project,
            to_project=ctx.project,
        ).copied_files

        staged_files = {f.name: f for f in staged_files}

        for sample in cohort.samples:
            for lane in sample.lanes:
                lane.fq1 = staged_files[lane.fq1]
                lane.fq2 = staged_files[lane.fq2]

    def set_metadata_in_bulk(cohort):
        "Sets metadata for all input files in bulk to save API calls"

        files_to_update, metadata_records = [], []
        for sample in cohort.samples:
            for lane in sample.lanes:
                files_to_update.extend([lane.fq1, lane.fq2])
                metadata_records.extend(
                    [{"sample_id": sample.id, "file_segment_number": lane.read_group}]
                    * 2
                )

        SetMetadataBulk(
            to_files=files_to_update,
            metadata=metadata_records,
            keep_old=True,
            name_="SetMetadata",
        )

    cohort = load(filename)
    return cohort
