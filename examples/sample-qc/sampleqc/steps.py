import tempfile
from freyja import Input, Output, Step, List
from hephaestus import File, UploadFile
from sampleqc.context import Context
from sampleqc.types import QCMetrics
from sampleqc.utils import bam_qc_metrics_ok


class CollectAndUploadQCSummary(Step):
    """Collects BAM QC metrics from all processed samples and uploads
    summary file in tab-separated format to SB project. Overwrites 
    existing file. Returns uploaded file object."""

    qc_metrics = Input(List[QCMetrics])
    uploaded_file = Output(File)

    def execute(self):

        # NOTE: don't create a transient temporary file (not thread safe)
        # because actual upload happens in another thread
        temp_filename = tempfile.gettempdir() + "/bam_qc_metrics.tsv"
        temp = open(temp_filename, "wt")

        # write header
        temp.write(
            "\t".join(
                [
                    "sample_id",
                    "bam_file",
                    "pct_pf_reads_aligned",
                    "strand_balance",
                    "status",
                ]
            )
            + "\n"
        )

        # write content
        for qc in self.qc_metrics:
            temp.write(
                "\t".join(
                    [
                        qc.bam_file.metadata["sample_id"],
                        qc.bam_file.name,
                        str(qc.pct_pf_reads_aligned),
                        str(qc.strand_balance),
                        "PASS" if bam_qc_metrics_ok(qc, self.config_) else "FAIL",
                    ]
                )
                + "\n"
            )
        temp.close()

        # upload file to platform (overwrites existing file)
        self.uploaded_file = UploadFile(
            local_path=temp.name, to_project=Context().project, overwrite=True
        ).file
