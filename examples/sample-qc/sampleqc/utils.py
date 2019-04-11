def bam_qc_metrics_ok(qc_metrics, config):
    """Returns true if alignment metrics pass quality cutoffs
    that are defined in config file"""

    return (
        qc_metrics.pct_pf_reads_aligned >= config.qc.min_pct_pf_reads_aligned
        and abs(qc_metrics.strand_balance) >= config.qc.min_strand_balance
    )
