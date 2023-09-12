Import-Module WhisperPS -DisableNameChecking

$modelPaths = @(
    "C:\Users\win10\Documents\podnotes-qa\api\Models\ggml-base.en.bin",
    "C:\Users\win10\Documents\podnotes-qa\api\Models\ggml-base-1.en.bin",
    "C:\Users\win10\Documents\podnotes-qa\api\Models\ggml-base-2.en.bin",
    "C:\Users\win10\Documents\podnotes-qa\api\Models\ggml-base-3.en.bin"
)
echo $args[0]

# $Model = Import-WhisperModel C:\Users\win10\Documents\podnotes-qa\api\Models\ggml-base.en.bin
for ($i = 0; $i -lt $modelPaths.count; $i++) {
  # Print the current element of the array
   try {    
            Write-Host $args[0]
            Write-Host $modelPaths[$i]
            $Model = Import-WhisperModel  $modelPaths[$i]
            cd  C:\Users\win10\Documents\podnotes-qa\workspace
            $Results = dir  $args[0]  | Transcribe-File $Model
            foreach ( $i in $Results ) { $txt = $i.SourceName + ".txt"; $i | Export-Text $txt; }
            foreach ( $i in $Results ) { $txt = $i.SourceName + ".ts.txt"; $i | Export-Text $txt -timestamps; }
        } catch {
            Write-Warning "Unable to use the model at  $modelPaths[$i] - most likely because it is busy. Trying next one."
        }
}


# cd  C:\Users\win10\Documents\podnotes-qa\workspace
# $Results = dir .\media.mp3 | Transcribe-File $Model
# foreach ( $i in $Results ) { $txt = $i.SourceName + ".txt"; $i | Export-Text $txt; }
# foreach ( $i in $Results ) { $txt = $i.SourceName + ".ts.txt"; $i | Export-Text $txt -timestamps; }