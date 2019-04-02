import logging, json, datetime
from collections import defaultdict
from freyja import Automation, Step, Input, Output, List, Optional
from hephaestus import FindOrImportFiles, SetMetadataBulk, ExportFiles, \
    FindOrCreateAndRunTask, File
from context import Context

class Main(Step):
    '''Example automation that imports FASTq files from volume, aligns 
    them with BWA, and exports resulting BAM files back to volume. 
    Inputs of the automation are name of the SB project, SB volume ID, 
    and volume source and destination directories. 
    Supports memoization, i.e. on re-run steps are only re-executed 
    if relevant changes are detected (for example new FASTq files added).
    
    To run this automation on your computer, type the following command
    while inside the project root directory:
    
      python -m app run --project_name <project-name> [--volume_id <volume-id> --src_dir <source-directory> --dest_dir <destination-directory>]
    '''

    project_name = Input(str, 
        description="Name of SB execution project")   
    volume_id = Input(str, 
        description="ID of volume for file import and export",
        default="external-demos/volumes_api_demo_bucket")
    src_dir = Input(str, 
        description="Source directory on volume containing input FASTq files",  
        default="")
    dest_dir = Input(str, 
        description="Target directory on volume where outputs will be exported to",
        default="automation/import-run-export/result")


    def execute(self):
        'step starts executing here'

        # initialize automation context with execution project and volume
        ctx = Context().initialize(self.project_name, self.volume_id)
                
        # import all fastq files found at volume source location
        fastq_paths = [
            l.location for l in ctx.volume.list(prefix=self.src_dir)
            if l.location.endswith(".fastq")
        ]
        
        import_step = FindOrImportFiles("FindOrImportFiles",
            filepaths=fastq_paths,
            from_volume=ctx.volume,
            to_project=ctx.project)

        # set metadata for each imported file and group files by sample ID
        samples = self.set_and_group_by_metadata(import_step.imported_files)
        
        # run BWA for each sample; samples are processed in parallel
        # because app outputs are promises and we can access them even
        # before output values become available (lazy evaluation)
        bams = []
        for sample_id, fastq_files in samples.items():
            bwa_mem = BWAmem(f"BWAmem-{sample_id}", 
                             input_reads=fastq_files)
            bams.append(bwa_mem.aligned_reads)

        # export all BAM files to volume; export step starts executing
        # as soon as all BAM files have become available
        ExportFiles("ExportFiles",
            files=bams,
            to_volume=ctx.volume,
            prefix=str(self.dest_dir),
            overwrite=True)
            
            
    def set_and_group_by_metadata(self, imported_files):
        '''sets metadata for each imported file based on file name and
        returns sample-to-file dict''' 
        
        metadata = []
        samples = defaultdict(list)
        
        for file in imported_files:
            
            # example filename: TCRBOA7-N-WEX-TEST.read1.fastq
            sample_id = file.name.split('-WEX')[0]
            paired_end = file.name.split('read')[1].split('.')[0]
            
            metadata.append({'sample_id':sample_id, 'paired_end':paired_end})
            samples[sample_id].append(file)
  
        # set metadata in bulk to minimize number of API calls          
        SetMetadataBulk("SetMetadataBulk",
            to_files=imported_files,
            metadata=metadata)
        
        return samples

class BWAmem(Step):
    input_reads = Input(List[File])
    aligned_reads = Output(File)
        
    def execute(self):
        ctx = Context()
        task = FindOrCreateAndRunTask(f"Run-{self.name_}",
            new_name = self.name_ + " - " + 
                datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            inputs={
                'input_reads' : self.input_reads,
                'reference_index_tar' : ctx.refs["bwa_bundle"]
            },
            app=ctx.apps["bwa"],
            in_project=ctx.project
        ).finished_task
    
        self.aligned_reads = task.outputs['aligned_reads']
        
if __name__ == '__main__':
    Automation(Main).run()
