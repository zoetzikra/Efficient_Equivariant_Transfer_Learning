# nlg-bias


### [The Woman Worked as a Babysitter: On Biases in Language Generation](https://arxiv.org/abs/1909.01326)

[Emily Sheng](https://ewsheng.github.io), [Kai-Wei Chang](http://web.cs.ucla.edu/~kwchang/), [Premkumar Natarajan](https://www.isi.edu/about/bio/prem_natarajan), [Nanyun Peng](http://vnpeng.net) (EMNLP 2019).

#### Data
`regard/` contains samples annotated with _regard_, and `sentiment/` contains samples  annotated with sentiment. 

The `train_other.tsv` files include samples with the "other" label. We use `train.tsv` to train the original models described in the paper, but also include the more robust models trained with `train_other.tsv` in this repo.

In the TSV files, the first column is the annotation (-1 for negative, 0 for neutral, 1 for positive, 2 for other), and the second column is the sample.

For more details on annotation guidelines and process, please look through the paper.

#### Models

_Update (Dec. 2020)_: Using more annotated data collected for our work [Towards Controllable Biases in Language Generation](https://github.com/ewsheng/controllable-nlg-biases), we have trained an updated [regard classifier](https://drive.google.com/file/d/1S5wG67U__3PrJddz_rS4Yr4Z45q_czOB/view?usp=sharing) (1GB) that you can download into `models/`.

This model consists of one BERT classifier (no ensemble) trained on 1.7K samples and has a (new) dev set acc. of 0.80 and a (new) test set acc. of 0.84. 
The model's accuracy on the (old) test set is 0.87 (comparable with the test set of the ensemble models below). 
This model can be run with the following command:
```
python scripts/run_classifier.py \
--data_dir data/regard \
--model_type bert \
--model_name_or_path models/bert_regard_v2_gpt2/checkpoint-300 \
--output_dir models/bert_regard_v2_gpt2 \
--max_seq_length 128 \
--do_predict \
--test_file [TEST_FILE] \
--do_lower_case \
--per_gpu_eval_batch_size 32 \
--model_version 2
```

---
_Older Models_: Each of these models are an ensemble of three BERT bert models and can be run with `scripts/eval.py` as detailed below.
- Download the _regard2_ model [here](https://drive.google.com/file/d/1XL0sTNVSS4Y3P8lgxg3tARdg6bz7tiO7/view?usp=sharing) (3.12 GB) into `models/`.
- Download the _regard1_ model [here](https://drive.google.com/file/d/10JBZb7lwOs0IONALZVhJJDdL9hpGaHiW/view?usp=sharing) (3.12 GB) into `models/`.
- Download the _sentiment2_ model [here](https://drive.google.com/file/d/1kJucHA2aYDDLChuObLQrRhR2zNz5qxnI/view?usp=sharing) (3.12 GB) into `models/`.
- Download the _sentiment1_ model [here](https://drive.google.com/file/d/1c9xtBfSUWt8XuqTC7RbtcEFCLBlbqj67/view?usp=sharing) (3.12 GB) into `models/`.

There are four types of models: _regard1_, _regard2_, _sentiment1_, and _sentiment2_. All are ensemble models that take the majority label of three model runs. _regard1_ and _sentiment1_ are trained on the respective `train.tsv` files (as described in the paper). _regard2_ and _sentiment2_ are trained on the respective `train_other.tsv` files. We recommend using _regard2_ and _sentiment2_, as they appear to be more quantitatively and qualitatively robust.

| model_type    | dev acc. | test acc. |
|---------------|----------|-----------|
| _regard2_     |  0.92    |  0.80     |
| _regard1_     |  0.85    |  0.77     |
| _sentiment2_  |  0.87    |  0.77     |
| _sentiment1_  |  0.77    |  0.77     |

#### Code
###### Setup
To create a clean environment and install necessary dependencies:

```conda create -n biases python=3.7```

```conda activate biases```

```conda install pip```

```conda install pytorch=1.2.0 -c pytorch```

```pip install -r requirements.txt```

###### Run models (using ensemble classifiers)
If we have a file of samples, e.g., `small_gpt2_generated_samples.tsv`, and a corresponding file where the demographic groups have been masked, `small_gpt2_generated_samples.tsv.XYZ`, we can run `eval.py`:

```python scripts/eval.py --sample_file data/generated_samples/sample.tsv --model_type regard2```

This will use the _regard2_ model to label all samples in `sample.tsv` and subsequently evaluate the amount of biases towards different demographics groups.