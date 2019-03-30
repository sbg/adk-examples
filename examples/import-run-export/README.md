Example automation that imports FASTq files from volume, aligns each pair of FASTq files with BWA, and exports resulting BAM files back to volume. 

Automation inputs are name of SB project, SB volume ID, and source and destination directories on the volume.

Prerequisites: To run this automation successfully, you need to have the Seven Bridges ADK installed. Please contact Seven Bridges if you need access to the ADK. You also need access to a [SB volume](https://docs.sevenbridges.com/docs/volumes) that is configured for read and write access.

To run this automation script on your computer, use following command inside project root directory:

```
python -m app run --project_name <project-name> [--volume_id <volume-id> --src_dir <source-directory> --dest_dir <destination-directory>]
```
Note that while the automation script executes locally, instantiated CWL apps will still be executed on the SB platform. Full local execution where also CWL apps execute on your own computer is currently not supported by the ADK.
