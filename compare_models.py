import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
import joblib
import torch
import torch.nn as nn
from torch.utils.data import DataLoader, TensorDataset
from torch.nn.utils.rnn import pad_sequence
from torchtext.vocab import vocab
from Baseline_Models.LSTM.LSTM import LSTMModel
from sklearn.metrics import accuracy_score
from transformers import pipeline
import os

class Config:

    TEST_DATA_PATH = 'Dataset/Testing_dataset/pre_processed_text_emotion_compressed.csv'

    NB_MODEL_PATH = 'Baseline_Models/Naive_Bayes/NaiveBayes_model_files/naive_bayes_model.joblib'
    NB_VECTORIZER_PATH = 'Baseline_Models/Naive_Bayes/NaiveBayes_model_files/tfidf_vectorizer.joblib'

    LSTM_MODEL_PATH = 'Baseline_Models/LSTM/LSTM_model_files/LSTM_model.pth'
    LSTM_VOCAB_PATH = 'Baseline_Models/LSTM/LSTM_model_files/vocab.pth'

    LLM_MODEL_PATH = ''

class NaiveBayesModel:

    def __init__(self):
        self.model , self.vectorizer =  None, None
        self.load_model_and_vectorizer(Config.NB_MODEL_PATH, Config.NB_VECTORIZER_PATH)

    def load_model_and_vectorizer(self, model_path, vectorizer_path):
        self.model = joblib.load(model_path)
        self.vectorizer = joblib.load(vectorizer_path)

    def make_predictions(self, new_data):
        new_data_vectorized = self.vectorizer.transform(new_data)
        predictions = self.model.predict(new_data_vectorized)
        return predictions
    
    def calculate_accuracy(self, predictions, true_labels):
        accuracy = (predictions == true_labels).mean()
        return accuracy

    def main(self, data):
        print('\nLoading the Naive Bayes model and vectorizer...')
        self.load_model_and_vectorizer(Config.NB_MODEL_PATH, Config.NB_VECTORIZER_PATH)
        print('Making predictions...')
        predictions = self.make_predictions(data['text'].astype(str).tolist())
        print('Calculating accuracy...')
        accuracy = self.calculate_accuracy(predictions, data['label'])
        print('Accuracy of the Naive Bayes model: ', accuracy*100)
        return accuracy

class LSTM:
    
    def __init__(self):
        self.model, self.vocab = None, None
        self.unknown_words_count = 0
        self.total_words_count = 0
        self.device = 'cuda:5' if torch.cuda.is_available() else torch.device("mps")

    def load_model_and_vocab(self, model_path, vocab_path):
        self.vocab = torch.load(vocab_path)
        self.model = LSTMModel(vocab_size=len(self.vocab), embedding_dim=100, hidden_dim=256, output_dim=6, n_layers=2, dropout=0.5).to(self.device)
        self.model.load_state_dict(torch.load(model_path, map_location=self.device))
        self.model.eval()

    def prepare_data(self, data):
        encoded_texts = []
        for text in data['text'].astype(str).tolist():
            encoded_text = []
            for word in text.split():
                self.total_words_count += 1
                if word in self.vocab:
                    encoded_text.append(self.vocab[word])
                else:
                    self.unknown_words_count += 1  # Increment if the word is not in the vocab
            encoded_texts.append(encoded_text)
        self.model.embedding.weight.data[self.vocab['<pad>']] = torch.zeros(100, device=self.device)
        text_tensor = [torch.tensor(x, dtype=torch.long, device=self.device) for x in encoded_texts]
        labels_tensor = torch.tensor(data['label'].tolist(), device=self.device)
        padded_texts = pad_sequence(text_tensor, batch_first=True, padding_value=self.vocab['<pad>'])
        prepared_data = TensorDataset(padded_texts, labels_tensor)
        data_loader = DataLoader(prepared_data, batch_size=128, shuffle=False)
        return data_loader

    def make_predictions(self, new_data):
        print('Preparing data...')
        data_loader = self.prepare_data(new_data)
        print(f'Unknown words encountered: {self.unknown_words_count} out of {self.total_words_count} words')
        print('Making predictions and Calculating accuracy...')
        total_accuracy = 0
        with torch.no_grad():
            for texts, labels in data_loader:
                texts, labels = texts.to(self.device), labels.to(self.device)
                outputs = self.model(texts, [len(x) for x in texts])
                predictions = outputs.argmax(dim=1, keepdim=True).squeeze()
                accuracy = accuracy_score(labels.cpu(), predictions.cpu())
                total_accuracy += accuracy
        return total_accuracy / len(data_loader)

    def main(self, data):
        print('\nLoading the LSTM model and vocabulary...')
        self.load_model_and_vocab(Config.LSTM_MODEL_PATH, Config.LSTM_VOCAB_PATH)
        accuracy = self.make_predictions(data)
        print('Accuracy of the LSTM model: ', accuracy*100)
        return accuracy

class LLM:

    def __init__(self):
        self.classifier = None
        self.candidate_labels = ['joy', 'sadness', 'anger', 'fear', 'love', 'surprise']
        self.candidate_labels_dict = {label: i for i, label in enumerate(self.candidate_labels)}
    
    def load_model(self, model_path):
        self.classifier = pipeline('zero-shot-classification', model=model_path)

    def main(self, data):
        print("\nLoading the LLM model...")
        self.load_model(Config.LLM_MODEL_PATH)
        print("Making predictions...")
        predictions = self.classifier(data['text'].astype(str).tolist(), self.candidate_labels, multi_label=False)
        predictions = [self.candidate_labels_dict[prediction['labels']] for prediction in predictions]
        print("Calculating accuracy...")
        accuracy = accuracy_score(data['label'], predictions)
        print("Accuracy of the LLM model: ", accuracy*100)
        return accuracy
        

def main():

    data = pd.read_csv(Config.TEST_DATA_PATH)

    nb_model = NaiveBayesModel()
    nb_accuracy = nb_model.main(data)
    lstm_model = LSTM()
    lstm_accuracy = lstm_model.main(data)
    llm_model = LLM()
    llm_accuracy = llm_model.main(data)

if __name__ == '__main__':
    main()