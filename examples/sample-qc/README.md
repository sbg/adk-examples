Automation processes multi-lanes FASTQ files into de-duplicated BAMs. Input for this automation is a sample manifest in tab-separated format that specifies sample IDs with corresponding FASTq files. When executed, the automation first finds or creates a project on the Seven Bridges platform into which it copies ("stages") all required files and apps. After setting all required file metadata, computation is performed by spawning platform tasks, one for each app execution step of the automation.

This example features both a static and dynamic conditional that implement QC checkpoints in a non-blocking manner.

Workflow Diagram below illustrated the steps for complete this NGS QC process: 


Starting from a sample manifest file that defines metadata around fastq files to be uploaded to seven bridges platform or already uploaded to the platform (see section 3.4 for manifest format examples),  the workflow first utilizes Tim Galore! (v0.4.4) to perform fastq reads QC and adapter trimming. If a user defined number of multiple lane fastq files from the same sample failed, the whole sample will be considered as failed and reports being generated. Only a defined percentage of fastq files from the same sample that have passed QC criteria such as quality filter will be sent to alignment step by BWA mem bundle(v0.1.17) and resulting alignment files from multiple lanes being merged by Sambamba Merge (v0.5.9). This alignment and BAM merge steps are handled solely by a CWL workflow and not an automation script, thus BWA can leverage the CWL scatter feature to align fastq files from multiple lanes. After merge, since each sample is represented by one alignment file, then Picard CollectAlignmentSummaryMetrics (v.1.140)  can now be used to generate alignment QC summary metrics at sample level. Again, only samples that passed alignment QC will be sent to next step such as Mark Duplicates using Picard MarkDuplicates (v1.140)  and further variant calling. Failed samples will be recorded and reported in a separate failure report.


To run this automation script on your computer, issue the following command inside project root directory:

```
python -m sampleqc run --manifest_filename manifest.tsv --config configs/sample_qc.yaml --project_name my_project

```

To successfully run this command, you need to have the Seven Bridges ADK installed. Please contact Seven Bridges if you need access to the ADK.

Note that while the automation script executes locally, instantiated CWL apps will still be executed on the SB platform. Full local execution where also CWL apps execute on your own computer is currently not supported by the ADK.

