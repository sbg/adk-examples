import logging, json, datetime
from freyja import Automation, Step, Input, Output, List, Optional
from hephaestus import (
    FindOrImportFiles,
    SetMetadataBulk,
    ExportFiles,
    FindOrCreateAndRunTask,
    File
)
from app.context import Context
from app.types import Sample

class Main(Step):
    """Example automation that imports FASTq files from volume, aligns 
    FASTq files with BWA, and exports resulting BAM files back to volume. 
    Inputs of the automation are name of the SB project, SB volume ID, 
    and volume source and destination directories. 
    
    To run this automation on your computer, type the following command
    while inside the project root directory:
    
      python -m app run --project_name <project-name> [--volume_id <volume-id> --src_dir <source-directory> --dest_dir <destination-directory>]
    """

    project_name = Input(str, description="Name of SB execution project")
    volume_id = Input(
        str,
        description="ID of volume for file import and export",
        default="external-demos/volumes_api_demo_bucket",
    )
    src_dir = Input(
        str,
        description="Source directory on volume containing input FASTq files",
        default="",
    )
    dest_dir = Input(
        str,
        description="Target directory on volume where outputs will be exported to",
        default="automation/import-run-export/result",
    )

    def execute(self):
        "Execution starts here."

        # initialize automation context with execution project and volume
        ctx = Context().initialize(self.project_name, self.volume_id)

        # stage input FASTq files and group them into samples
        samples = ImportFiles(src_dir=self.src_dir).samples
        
        # run BWA for each sample; samples are processed in parallel
        # because app outputs are promises and we can access them
        # before output values become available (lazy evaluation)
        bams = []
        for sample in samples:
            bwa = BWAmem(
                f"BWAmem-{sample.sample_id}", 
                input_reads=sample.fastq_files
            )
            bams.append(bwa.aligned_reads)

        # export all BAM files to volume; export step starts executing
        # as soon as all BAM files have become available
        ExportFiles(
            files=bams, to_volume=ctx.volume, prefix=self.dest_dir, overwrite=True
        )

class ImportFiles(Step):
    '''Finds FASTq files on volume, imports them into project, sets file 
    metadata, and returns updated files grouped into list of samples'''
    
    src_dir = Input(str)
    samples = Output(List[Sample])
    
    def execute(self):
        imported_files = self.import_files_from_volume()
        updated_files = self.update_file_metadata(imported_files)
        self.samples = self.group_files_into_samples(updated_files)
        
    def import_files_from_volume(self):
        'Imports all fastq files found at volume source location'
        
        volume = Context().volume
        
        fastq_paths = [
            l.location
            for l in volume.list(prefix=self.src_dir)
            if l.location.endswith(".fastq")
        ]

        return FindOrImportFiles(
            filepaths=fastq_paths, 
            from_volume=volume, 
            to_project=Context().project
        ).imported_files
        
    def update_file_metadata(self, files):
        '''Sets file metadata in bulk for list of files based on file names.
        Setting metadata in bulk instead of per-file reduces API calls.
        Example filename: TCRBOA7-N-WEX-TEST.read1.fastq'''

        metadata = []
        for file in files:
            sample_id = file.name.split("-WEX")[0]
            paired_end = file.name.split("read")[1].split(".")[0]
            metadata.append({"sample_id": sample_id, "paired_end": paired_end})

        return SetMetadataBulk(
            to_files=files, metadata=metadata
        ).updated_files

        
    def group_files_into_samples(self, files):
        '''Groups files into list of sample objects for easier downstream
        processing.'''
        
        samples = {}
        for file in files:
            sample_id = file.metadata["sample_id"]
            if sample_id not in samples:
                samples[sample_id] = Sample(sample_id)
            samples[sample_id].fastq_files.append(file)

        return list(samples.values())
    

class BWAmem(Step):
    """App wrapper step that runs BWA-MEM on SB platform. 
    Names task after sample ID metadata."""

    input_reads = Input(List[File])
    aligned_reads = Output(File)

    def execute(self):
        ctx = Context()
        task = FindOrCreateAndRunTask(
            new_name="BWAmem - " 
                + self.input_reads[0].metadata["sample_id"] + " - "
                + datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            inputs={
                "input_reads": self.input_reads,
                "reference_index_tar": ctx.refs["bwa_bundle"],
            },
            app=ctx.apps["bwa"],
            in_project=ctx.project,
        ).finished_task

        self.aligned_reads = task.outputs["aligned_reads"]


if __name__ == "__main__":
    Automation(Main).run()
