Example automation that processes multi-lane FASTq files into de-duplicated BAM files, with built-in QC checkpoints. Input for this automation is a sample manifest in tab-separated format that specifies sample IDs with corresponding FASTq filenames.

This example features both a static and dynamic conditional that implement QC checkpoints in a non-blocking manner.

NOTE: To successfully run this automation example, you need to have the Seven Bridges RHEO Automation Development Kit (ADK) installed. Please contact Seven Bridges if you need access to the ADK. Required minimum versions of ADK libraries are Freyja version 0.18.1 and Hephaestus version 0.16.0.

The below **[Workflow Diagram](https://github.com/sbg/adk-examples/blob/master/examples/sample-qc/Multi-Lane-sample-QC-diagram.png)** illustrates the steps to complete this NGS Sample QC process: 

![](Multi-Lane-sample-QC-diagram.png)

Starting from a sample **[manifest file](https://github.com/sbg/adk-examples/blob/master/examples/sample-qc/manifest.tsv)** which defines the metadata of fastq files to be uploaded or already uploaded to the platform,  the workflow first utilizes [Trim Galore! (v0.4.4)](https://igor.sbgenomics.com/public/apps#admin/sbg-public-data/trim-galore/) to perform fastq reads QC and adapter trimming. If a certain number(user defined) of multiple-lane fastq files from the same sample failed, the whole sample will be considered as failed and reports being generated. Only when a certain (configurable) percentage of files from the same sample have passed QC criteria, this sample is sent to alignment step using [BWA mem bundle(v0.1.17)](https://igor.sbgenomics.com/public/apps#admin/sbg-public-data/bwa-mem-bundle-0-7-17/). 

The resulting alignment files from multiple lanes being merged by [Sambamba Merge (v0.5.9)](https://igor.sbgenomics.com/public/apps#admin/sbg-public-data/sambamba-merge-0-5-9/). This alignment and BAM merge steps are handled solely by a CWL workflow and not an automation script, thus BWA can leverage the CWL scattering feature to align fastq files from multiple lanes in parallel jobs (optimization). 

After merge, since each sample is represented by just one alignment file, then [Picard CollectAlignmentSummaryMetrics (v.1.140)](https://igor.sbgenomics.com/public/apps#admin/sbg-public-data/picard-collectalignmentsummarymetrics-1-140/) can now be used to generate alignment QC summary metrics at sample level. Again, only samples that passed alignment QC will be sent to next step such as Mark Duplicates using [Picard MarkDuplicates (v1.140)](https://igor.sbgenomics.com/public/apps#admin/sbg-public-data/picard-markduplicates-1-140/) and other further downstream analysis such as variant calling. Failed samples will be recorded and reported in a separate failure report. This conditional judgement is one of the features that automation handles easily compared to CWL.

System settings, user defined parameters, and run specific settings (apps, path, QC criteria) can be defined and changed easily in a **[Settings File](https://github.com/sbg/adk-examples/blob/master/examples/sample-qc/configs/sample_qc.yaml)** in YAML format. Settings can be changed at runtime without changing the source code of the automation or without re-deploying the automation on the Seven Bridges Platform.

To run this automation script on your local computer, issue the following command from inside project root directory:

```
$ python -m sampleqc run --project_name <sb_project_name> [--manifest_file <sb_file_id>]
```

whereas `<sb_project_name>` refers to name of a SB project within which processing will take place, and `<sb_file_id>` is the file ID of the manifest file stored on the SB platform (upload this file first if necessary). If a project with specified name is found, it re-uses this project and all the analysis results already in this project (memoization). Otherwise, a new project with that name is created.

Note that only the automation script executes locally. CWL apps are still being executed on the SB platform. Full local execution where both automation script and CWL apps execute locally or on an HPC is currently not supported by the ADK.

In order to run an automation on the SB platform, the automation source code needs to be first compressed into a code package file (.zip format) and then uploaded to the Seven Bridges Platform. Please refer to our **[tutorial](https://docs.sevenbridges.com/docs/deploy-and-run-automations-on-the-seven-bridges-platform)** for a step-by-step guide about how to **deploy code packages** and **run automations** on the Seven Bridges Platform.
