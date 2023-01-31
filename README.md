# TheraBot

A Telegram chatbot for therapy.
This repository contains the code to run the chatbot developed in the Ph.D. thesis "[Generative Empathetic Data-Driven Conversational Agents for Mental Healthcare](https://www.overleaf.com/read/bvfznvsnrgdc)".

## Repository structure

This repository is organised into four main directories:

- `experiments/` contains the directories to host:  
    - logs of execution.
- `resources/` contains:
    - directory to host the YAML configuration files to run the service.
    - directory to host the pre-trained models, and the references to download them.
- `src/` contains modules and scripts to: 
    - run the telegram bot;
    - interact with the text-based models;
    - interact with the speech-based models.

For further details, refer to the `README.md` within each directory.

## Environment

### Python environment

To install all the required packages within an anaconda environment, run the following commands:

```bash
# Create anaconda environment (skip cudatoolkit option if you don't want to use the GPU)
conda create -n therabot python=3.10 cudatoolkit=11.6
# Activate anaconda environment
conda activate therabot
# Install packages
pip install -r requirements.txt
```

To add the source code directory to the Python path, you can add this line to the file `~/.bashrc`

```bash
export PYTHONPATH=$PYTHONPATH:/path/to/chatbot/src
```

### Additional submodules

This repository was built re-using the code of other submodules.
To install and ka

```bash
# Download and initialise submodules
git submodule init; git submodule update
cd submodules/tts_mellotron_api
git submodule init; git submodule update
cd submodules/mellotron
git submodule init; git submodule update
# Get back to repository root
cd ../../../..
```

To add the submodules directories to the Python path, you can add these lines to the file `~/.bashrc`

```bash
export PYTHONPATH=$PYTHONPATH:/path/to/chatbot/submodules/programmable_chatbot/src
export PYTHONPATH=$PYTHONPATH:/path/to/chatbot/submodules/dldlm/src
export PYTHONPATH=$PYTHONPATH:/path/to/chatbot/submodules/dialogue_gst/src
export PYTHONPATH=$PYTHONPATH:/path/to/chatbot/submodules/tts_mellotron_api/src
export PYTHONPATH=$PYTHONPATH:/path/to/chatbot/submodules/tts_mellotron_api/submodules/mellotron
export PYTHONPATH=$PYTHONPATH:/path/to/chatbot/submodules/tts_mellotron_api/submodules/mellotron/waveglow
export PYTHONPATH=$PYTHONPATH:/path/to/chatbot/submodules/tts_mellotron_api/submodules/tacotron2
```

## Service

### Run

There is a script to run the chatbot service, it expects to have `./src` in the Python path and all models to be downloaded and placed in the `./resources/data/raw/` directory.

To run in foreground execute:
```bash
python ./src/bin/main.py --config_file_path ./resources/configs/path/to/config.yaml
```

To run in background execute:
```bash
nohup python ./src/bin/main.py --config_file_path ./resources/configs/path/to/config.yaml > experiment_"$(date '+%Y_%m_%d_%H_%M_%S')".out &
```

### Stop

To stop in foreground enter `[Ctrl + C]`

To stop in background, knowing the pid
```bash
kill -SIGINT <pid>
```

To get the pid run 
```bash
ps -elf | grep main.py
```

## References

If you are willing to use our code or our models, please cite our work through the following BibTeX entry:

```bibtex
@phdthesis{DBLP:phd/it/Scotti23,
  author    = {Vincenzo Scotti},
  title     = {Generative Empathetic Data-Driven Conversational Agents for Mental Healthcare},
  school    = {Polytechnic University of Milan, Italy},
  year      = {2023},
  url       = {T.B.D.}
}
```
