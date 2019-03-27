Example automation that implements a parallelized version of a text file word counter. 
This example runs locally and does not depend on the Seven Bridges platform for execution.

### Run locally

Change directory into the `wordcount` subdirectory and type

```
python wordcount.py run --file_name words.txt
```

If successful, the following output should appear on your screen:

```
2019-01-16 16:10:39,234    INFO [  freyja.log:  67]: (MainThread  ) Logging configured
2019-01-16 16:10:39,235    INFO [freyja.graph: 373]: (MainThread  ) Process: 14307
2019-01-16 16:10:39,235    INFO [freyja.graph: 549]: (MainThread  ) Instantiating Step <Main "main">
2019-01-16 16:10:39,235    INFO [freyja.graph: 232]: (MainThread  ) Step <Main ("main")> queued for execution
2019-01-16 16:10:39,235    INFO [freyja.graph: 709]: (main        ) Initiating execution for for: Step <Main ("main")>
2019-01-16 16:10:39,236    INFO [freyja.graph: 719]: (main        ) Execution started for: Step <Main ("main")>
2019-01-16 16:10:39,237    INFO [freyja.graph: 725]: (main        ) RUNNING: main
2019-01-16 16:10:39,237    INFO [freyja.graph: 549]: (main        ) Instantiating Step <WordCounter "counter0">
2019-01-16 16:10:39,237    INFO [freyja.graph: 232]: (main        ) Step <WordCounter ("main.counter0")> queued for execution
2019-01-16 16:10:39,237    INFO [freyja.graph: 549]: (main        ) Instantiating Step <WordCounter "counter1">
2019-01-16 16:10:39,238    INFO [freyja.graph: 709]: (main.counter0) Initiating execution for for: Step <WordCounter ("main.counter0")>
2019-01-16 16:10:39,238    INFO [freyja.graph: 232]: (main        ) Step <WordCounter ("main.counter1")> queued for execution
2019-01-16 16:10:39,238    INFO [freyja.graph: 719]: (main.counter0) Execution started for: Step <WordCounter ("main.counter0")>
2019-01-16 16:10:39,239    INFO [freyja.graph: 549]: (main        ) Instantiating Step <WordCounter "counter2">
2019-01-16 16:10:39,239    INFO [freyja.graph: 725]: (main.counter0) RUNNING: counter0
2019-01-16 16:10:39,239    INFO [freyja.graph: 709]: (main.counter1) Initiating execution for for: Step <WordCounter ("main.counter1")>
2019-01-16 16:10:39,240    INFO [freyja.graph: 719]: (main.counter1) Execution started for: Step <WordCounter ("main.counter1")>
2019-01-16 16:10:39,240    INFO [freyja.graph: 725]: (main.counter1) RUNNING: counter1
2019-01-16 16:10:39,240    INFO [freyja.graph: 232]: (main        ) Step <WordCounter ("main.counter2")> queued for execution
2019-01-16 16:10:39,241    INFO [freyja.graph: 756]: (main.counter0) Execution finished for: Step <WordCounter ("main.counter0")>
2019-01-16 16:10:39,242    INFO [freyja.graph: 756]: (main.counter1) Execution finished for: Step <WordCounter ("main.counter1")>
2019-01-16 16:10:39,243    INFO [freyja.graph: 709]: (main.counter2) Initiating execution for for: Step <WordCounter ("main.counter2")>
2019-01-16 16:10:39,243    INFO [freyja.graph: 719]: (main.counter2) Execution started for: Step <WordCounter ("main.counter2")>
2019-01-16 16:10:39,244    INFO [freyja.graph: 725]: (main.counter2) RUNNING: counter2
2019-01-16 16:10:39,245    INFO [freyja.graph: 756]: (main.counter2) Execution finished for: Step <WordCounter ("main.counter2")>
2019-01-16 16:10:39,245    INFO [        root:  23]: (main        ) Found 9 words.
2019-01-16 16:10:39,246    INFO [freyja.graph: 756]: (main        ) Execution finished for: Step <Main ("main")>
2019-01-16 16:10:39,246    INFO [freyja.graph: 108]: (Executor-main) Executor done
2019-01-16 16:10:39,246    INFO [freyja.graph: 418]: (MainThread  ) 
-----------------------------------------------------------------------
Execution summary:
    Steps instantiated: 4
    Steps incomplete:   0
    Steps executed:     4
    Steps failed:       0
-----------------------------------------------------------------------
```
