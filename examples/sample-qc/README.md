Automation processing multi-lanes FASTq files into de-duplicated BAMs for a set of samples. Input for this automation is a sample manifest in tab-separated format that specifies sample IDs with corresponding FASTq filenames.

This example features both a static and dynamic conditional that implement QC checkpoints in a non-blocking manner.

To run this automation script on your computer, use following command inside project root directory:

```
python -m sampleqc run --manifest_filename manifest.tsv --config configs/sample_qc.yaml --project_name my_project

```

Note that while the automation script executes locally, instantiated CWL apps will still be executed on the SB platform. Full local execution where also CWL apps execute on your own computer is currently not supported by the ADK.

