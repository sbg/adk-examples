Automation processing multi-lane FASTq files into de-duplicated BAMs. Input for this automation is a sample manifest in tab-separated format that specifies sample IDs with corresponding FASTq files. When executed, the automation first finds or creates a project on the Seven Bridges platform into which it copies ("stages") all required files and apps. After setting all required file metadata, computation is performed by spawning platform tasks, one for each app execution step of the automation.

### Run automation script locally

This is the preferred method while the automation is still under development.
It allows for very quick debugging and testing. Note that local execution is actually
a 'hybrid' mode, where the automation script itself runs locally while it still
relies on the Seven Bridges platform for finding files and executing apps.

This automation uses `hephaestus`, which in turn uses the Seven Bridges API to talk to the
platform. To successfully authenticate against the API, the developer token needs
to be stored locally on the computer where this automation runs. Please follow
our [API documentation](https://sevenbridges-python.readthedocs.io/en/latest/quickstart/#initializing-the-library) to see how this is accomplished.

Make sure you are within the sample_qc project directory of the automation repo, then type:

```
python -m sampleqc run --manifest_filename manifest.tsv --config configs/sample_qc.yaml --project_name my_project

```

### Deploy and run automation on the Seven Bridges platform

For platform deployment, follow the following steps:
1) Create a code package file using the `freyja pack` command.
2) Upload the code package file (`.zip` format) to the SB platform and note ID of this file. You can upload the code package file into any project. However, you must not delete or lose access to this file, or your automation will stop working.
3) Use the `sb automations create` command of the SB CLI to create a new automation entity, or note the ID of an already existing automation entity using the `sb automations list` command.
4) Use the `sb automations members create` command of the SB CLI to add users or teams that should have access to this automation. READ, COPY, WRITE, and EXEC permissions are required to successfully run an automation.
5) Use the `sb automations packages create` command of the SB CLI to create a new code package entity under above automation entity and with file ID of uploaded code package file.

After deploying the code package, you will be able to execute the automation on the SB platform using the following SB CLI command:

```
sb automations start --automation-name sampleQC --inputs '{"manifest_filename": "sb://5be3b65ae4b05ad86554ac29", "project_name": "adk-sampleQC"}'
```

This mode of execution does not depend on your local computer, so you can
shut it down after an automation has been started.

### Deploy as 'launcher app' on SB platform

*Disclaimer: Note that this is not officially supported. Ultimately, automations
are run on the Seven Bridges platform using their own frontend,
which is currently under development.* 

Make sure you are within the root directory of the automation repo, then type:

```
python demos/fastq2bam/launcher.py --project_name "<app-project-name>"
```
If successful, this will put a CWL tool named `Fastq2Bam` inside the specified project. This allows other users to run this automation like any other CWL app directly on the platform, without using any terminal.
