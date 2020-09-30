Example automation that imports FASTq files from a specified cloud bucket location, aligns them with BWA, and exports resulting BAM files back to another cloud bucket location. 

Automation inputs are the name of the SB project in which data processing should take place, the source directory on the cloud bucket containing the input FASTq files, and the target directory on the cloud bucket into which aligned BAM files should be exported. If a project with the specified name already exists, this existing project and analysis results therein are re-used during execution (memoization). Otherwise, a new project is created.

Prerequisites: This example requires the Seven Bridges RHEO Automation Development Kit (ADK). Please contact Seven Bridges if you need access to the ADK. You also need access to at least one [SB volume](https://docs.sevenbridges.com/docs/volumes) that is configured for read and write access.

To run this automation from your local computer, use the following command from inside the project root directory:

```
python -m app run --project_name <project-name> [--src_dir <location>] [--dest_dir <location>]
```
   
whereas `<location>` refers to a cloud bucket directory in format `<sb-volume-id>:<bucket-prefix>`. If not provided, location defaults as specified in the automation code are used.

Requires Freyja version 0.18.1 (or higher) and Hephaestus version 0.16.0 (or higher). 

Note that only the automation script executes locally. CWL apps are still being executed on the SB platform. Full local execution where both automation script and CWL apps execute locally or on an HPC is currently not supported by the ADK.
