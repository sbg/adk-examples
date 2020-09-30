Example automation that imports whole-exome sequencing (WES) FASTq tumor-normal pairs from a configurable cloud bucket location, calls somatic mutations after passing a minimum (configurable) coverage criterion, and exports resulting VCF files back to a configurable cloud bucket location. Also generates MultiQC reports summarizing various quality metrics across the cohort. 

This automation example is meant for execution on the Seven Bridges Platform via the [RHEO visual interface](https://docs.sevenbridges.com/docs/manage-via-the-visual-interface).

# Prerequisites

Requires Python libraries Freyja version 0.18.3 (or higher) and Hephaestus version 0.16.5 (or higher), both of which are part of the Seven Bridges RHEO Automation Development Kit (ADK). Please contact Seven Bridges if you need access to the ADK. The automation also requires access to at least one [SB volume](https://docs.sevenbridges.com/docs/volumes) that is configured for read and write access and that contains FASTq files in a single input folder.  

The pre-configured dataset used by this example is from the Texas Cancer Research Biobank (TCRB). Alignment and variant calling is performed using the BMS Public Apps available on the Seven Bridges Platform.

CWL apps used by this automation include:
* BMS BAM Prep: https://igor.sbgenomics.com/u/bristol-myers-squibb-publishin/bms-public-apps/apps/#bristol-myers-squibb-publishin/bms-public-apps/bms-bam-prep/2
* BMS WES Tumor-Normal pipeline hg19: https://igor.sbgenomics.com/u/bristol-myers-squibb-publishin/bms-public-apps/apps/#bristol-myers-squibb-publishin/bms-public-apps/bms-wes-tumor-normal-pipeline-hg19/2
* MultiQC: https://igor.sbgenomics.com/public/apps#admin/sbg-public-data/multiqc-1-9/2

# TCRB disclaimer

The Texas Cancer Research Biobank (TCRB) and Baylor College of Medicine Human Genome Sequencing Center (BCM-HGSC) have sequenced tumor and normal genomes of patients who consented to make their data broadly available for biomedical research under the condition that end users never attempt to re-identify participants.

Further details about the consented cases can be found at: http://www.txcrb.org/data.html

These tumor and normal specimen BAM, somatic variant MAF and germline MAF files are available for each consented patient as described on the Open Access Privacy page: http://www.txcrb.org/privacy.html

These data are made available with consent from participants for the aim of advancing biomedical science. By receiving these data you have agreed to the following conditions of use:

Redistribution of any part of these data will include a copy of this notice.
* These data are intended for use as learning and/or research tools.
* These data in part or in whole may be freely downloaded, used in analyses and repackaged in databases.
* No attempt to identify any specific individual represented by these data will be made.
* No attempt will be made to compare and/or link this public data set in part or in whole to private health information.
* This data set is not intended for direct profit of anyone who receives it and may not be resold.
* Users are free to use the data in scientific publications if the providers of the data (Texas Cancer Research Biobank and Baylor College of Medicine Human Genome Sequencing Center) are properly acknowledged.
 
