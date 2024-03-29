#!/usr/bin/env python3

from Libraries import *
from HelperFunctions import getLabels, extractList
from ModelFunctions import TFSentenceTransformer, E2ESentenceTransformer

def importUMD(UMD_path, anno_type, task_type=None):
    chunksize = 10 ** 6

    if anno_type == "crowd":
        ## For Train

        # Get all posts
        tfr = pd.read_csv(os.path.join(UMD_path, anno_type, "train", "shared_task_posts.csv"), chunksize=chunksize,
                          iterator=True)
        all_train_posts = pd.concat(tfr, ignore_index=True)

        # Get Labels
        train_labels = pd.read_csv(os.path.join(UMD_path, anno_type, "train", "crowd_train.csv"))

        # Get appropriate task posts; if none provided, ignore
        if task_type.upper() in (["A", "B", "C"]):
            train_task_nexus = pd.read_csv(
                os.path.join(UMD_path, anno_type, "train", f"task_{task_type.upper()}_train.posts.csv"))

        # Get all posts in task
        task_train = all_train_posts[all_train_posts.post_id.isin(train_task_nexus.post_id)]
        # Add Labels
        task_train = pd.merge(task_train, train_labels, how="left", on="user_id")

        ## For Test

        # # Get all posts
        tfr = pd.read_csv(os.path.join(UMD_path, anno_type, "test", "shared_task_posts_test.csv"), chunksize=chunksize,
                          iterator=True)
        all_test_posts = pd.concat(tfr, ignore_index=True)

        # Get Labels
        test_labels = pd.read_csv(os.path.join(UMD_path, anno_type, "test", "crowd_test.csv"))

        # Get appropriate task posts; if none provided, ignore
        if task_type.upper() in (["A", "B", "C"]):
            test_task_nexus = pd.read_csv(
                os.path.join(UMD_path, anno_type, "test", f"task_{task_type.upper()}_test.posts.csv"))

        # Get all posts in task
        task_test = all_test_posts[all_test_posts.post_id.isin(test_task_nexus.post_id)]
        # Add Labels
        task_test = pd.merge(task_test, test_labels, how="left", on="user_id")

        return task_train, task_test

    elif anno_type == "expert":
        # Get all posts
        tfr = pd.read_csv(os.path.join(UMD_path, anno_type, "expert_posts.csv"), chunksize=chunksize,
                          iterator=True)
        expert_posts = pd.concat(tfr, ignore_index=True)
        # Get Labels
        expert_labels = pd.read_csv(os.path.join(UMD_path, anno_type, "expert.csv"))
        # Add Labels
        all_expert_posts = pd.merge(expert_posts, expert_labels, how="left", on="user_id")

        return all_expert_posts


def importCSSRS(filepath, num_labels=4):
    CSSRS = pd.read_csv(filepath)
    CSSRS, inv_map = getLabels(CSSRS, num_labels, "CSSRS")
    # Extract List from string
    extractList(CSSRS)
    # Concatenate Posts into one long string
    CSSRS["Post"] = CSSRS["Post"].apply(lambda x: " ".join(x))
    return CSSRS


def getModel(modelType):
    if modelType.upper() == "BERT":
        model_name = 'bert-base-uncased'
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = BertForMaskedLM.from_pretrained(model_name)
    elif modelType.upper() == "ROBERTA":
        model_name = 'roberta-base'
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = RobertaForMaskedLM.from_pretrained(model_name)
    elif modelType.upper() == "ELECTRA":
        if platform.system() == "Windows":
            model_name = 'google/electra-base-discriminator'
        elif platform.system() == "Linux":
            model_name = r'/ddn/home12/r3102/files/electra-base-discriminator'
        tokenizer = AutoTokenizer.from_pretrained(model_name)
        model = ElectraForMaskedLM.from_pretrained(model_name)

    return tokenizer, model

def getRegularModel(modelName, modelType, CSSRS_n_label):


    if modelName.upper() == "BERT":
        model_name = 'bert-base-uncased'
        if modelType == "transformer":
            model = TFBertForSequenceClassification.from_pretrained(model_name,num_labels = CSSRS_n_label)
        else:
            model = BertModel.from_pretrained(model_name)
    elif modelName.upper() == "ROBERTA":
        model_name = 'roberta-base'
        if modelType == "transformer":
            model = TFRobertaForSequenceClassification.from_pretrained(model_name,num_labels = CSSRS_n_label)
        else:
            model = RobertaModel.from_pretrained(model_name)
    elif modelName.upper() == "ELECTRA":
        if platform.system() == "Windows":
            model_name = 'google/electra-base-discriminator'
        elif platform.system() == "Linux":
            model_name = r"/ddn/home12/r3102/files/electra-base-discriminator"
        if modelType == "transformer":
            model = TFElectraForSequenceClassification.from_pretrained(model_name,num_labels = CSSRS_n_label)
        else:
            model = ElectraModel.from_pretrained(model_name)

    elif modelName.upper() == "SBERT":
        if platform.system() == "Windows":
            model_name = 'sentence-transformers/all-mpnet-base-v2'
        elif platform.system() == "Linux":
            model_name = r"/ddn/home12/r3102/files/all-mpnet-base-v2"

        model = E2ESentenceTransformer(model_name, CSSRS_n_label)
        # model = TFSentenceTransformer(model_name)
        # model = SentenceTransformer(model_name)
    return model

def getMultiTaskModel(model_name, model_path, modelType, transferLearning, CSSRS_n_label):
    if model_name == "sBERT":
        model = getRegularModel(model_name, modelType, CSSRS_n_label)
        return model

    if transferLearning:  # If applying model trained using MLM pre-training
        if os.path.exists(model_path):  # If MLM pre-trained model exists for BERT model
            if model_name == "BERT":
                if modelType == "transformer":  # If only dropout and output top layers
                    model = TFBertModel.from_pretrained(model_path)

            elif model_name == "ROBERTA":
                if modelType == "transformer":  # If only dropout and output top layers
                    model = TFRobertaModel.from_pretrained(model_path)

            elif model_name == "ELECTRA":
                if modelType == "transformer":  # If only dropout and output top layers
                    model = TFElectraModel.from_pretrained(model_path)

        else:  # If No MLM pre-trained model exists for selected model
            print(f"No MLM pre-trained model exists for {model_name}. "
                  f"No transfer learning applied. Loading from huggingface checkpoint.")
            model = getRegularModel(model_name, modelType, CSSRS_n_label)

    else:
        print(f"No transfer learning applied. Loading from huggingface checkpoint.")
        if model_name == "BERT":
            model_name = 'bert-base-uncased'
            if modelType == "transformer":  # If only dropout and output top layers
                model = TFBertModel.from_pretrained(model_name)

        elif model_name == "ROBERTA":
            model_name = 'roberta-base'
            if modelType == "transformer":  # If only dropout and output top layers
                model = TFRobertaModel.from_pretrained(model_name)

        elif model_name == "ELECTRA":
            if platform.system() == "Windows":
                model_name = 'google/electra-base-discriminator'
            elif platform.system() == "Linux":
                model_name = r"/ddn/home12/r3102/files/electra-base-discriminator"
            if modelType == "transformer":  # If only dropout and output top layers
                model = TFElectraModel.from_pretrained(model_name)

    return model

def getMainTaskModel(model_name, model_path, modelType, transferLearning, CSSRS_n_label):

    if model_name == "sBERT":
        model = getRegularModel(model_name, modelType, CSSRS_n_label)
        return model

    if transferLearning:  # If applying model trained using MLM pre-training
        if os.path.exists(model_path):  # If MLM pre-trained model exists for BERT model
            if model_name == "BERT":
                if modelType == "transformer":  # If only dropout and output top layers
                    model = TFBertForSequenceClassification.from_pretrained(model_path, from_pt=True,
                                                                            num_labels=CSSRS_n_label)
                else:
                    model = BertModel.from_pretrained(model_path)

            elif model_name == "ROBERTA":
                if modelType == "transformer":  # If only dropout and output top layers
                    model = TFRobertaForSequenceClassification.from_pretrained(model_path, from_pt=True,
                                                                               num_labels=CSSRS_n_label)
                else:
                    model = RobertaModel.from_pretrained(model_path)

            elif model_name == "ELECTRA":
                if modelType == "transformer":  # If only dropout and output top layers
                    model = TFElectraForSequenceClassification.from_pretrained(model_path, from_pt=True,
                                                                               num_labels=CSSRS_n_label)
                else:
                    model = ElectraModel.from_pretrained(model_path)

        else:  # If No MLM pre-trained model exists for selected model
            print(f"No MLM pre-trained model exists for {model_name}. "
                  f"No transfer learning applied. Loading from huggingface checkpoint.")
            model = getRegularModel(model_name, modelType, CSSRS_n_label)

    else:
        print(f"No transfer learning applied. Loading from huggingface checkpoint.")
        model = getRegularModel(model_name, modelType, CSSRS_n_label)

    return model

def getTokenizer(modelType):
    if modelType.upper() == "BERT":
        model_name = 'bert-base-uncased'
        tokenizer = AutoTokenizer.from_pretrained(model_name)
    elif modelType.upper() == "ROBERTA":
        model_name = 'roberta-base'
        tokenizer = AutoTokenizer.from_pretrained(model_name)
    elif modelType.upper() == "ELECTRA":
        if platform.system() == "Windows":
            model_name = 'google/electra-base-discriminator'
        elif platform.system() == "Linux":
            model_name =  r"/ddn/home12/r3102/files/electra-base-discriminator"
        tokenizer = AutoTokenizer.from_pretrained(model_name)
    elif modelType.upper() == "SBERT":
        if platform.system() == "Windows":
            model_name = 'sentence-transformers/all-mpnet-base-v2'
        elif platform.system() == "Linux":
            model_name = r"/ddn/home12/r3102/files/all-mpnet-base-v2"
        tokenizer = AutoTokenizer.from_pretrained(model_name)

    return tokenizer
