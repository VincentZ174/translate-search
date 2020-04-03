import sys
from PyQt5.QtWidgets import QTextBrowser, QWidget, QDesktopWidget, QApplication, QPlainTextEdit, QComboBox, QLabel, QMainWindow, QApplication, QPushButton
from PyQt5 import QtGui
from PyQt5.QtCore import QRect, Qt, QSize
import boto3
import os
os.environ['PYGAME_HIDE_SUPPORT_PROMPT'] = "hide"
import pygame
import time
import pandas as pd
import requests
import urllib
from bs4 import BeautifulSoup
import requests

os.system('cls' if os.name == 'nt' else 'clear')

df_translate = pd.read_csv('TranslateTextCodes.csv', header=None)
df_polly = pd.read_csv('PollyCodes.csv', header=None)
df_voices = pd.read_csv('PollyVoices.csv', header=None)

awsTranslateCodes = {}
pollyCodes = {}
pollyVoices = {}

for i, j in df_translate.iterrows():
    awsTranslateCodes[j[0].lower()] = j[1]

for i, j in df_polly.iterrows():
    pollyCodes[j[0].lower()] = j[1]

for i, j in df_voices.iterrows():
    pollyVoices[j[0].lower()] = j[1]

translate = boto3.client('translate')
polly = boto3.client('polly')
comprehend = boto3.client('comprehend')

class Window(QMainWindow):
    def __init__(self):
        super().__init__()
        self.initUI()


    def center(self):
        qr = self.frameGeometry()
        cp = QDesktopWidget().availableGeometry().center()
        qr.moveCenter(cp)
        self.move(qr.topLeft())

    def initUI(self):
        self.title = "Translate Search"
        self.left = 1000
        self.top = 400
        self.width = 850
        self.height = 475
        self.fromLang = 'afrikaans'
        self.toLang = 'afrikaans'

        self.setWindowTitle(self.title)
        self.setGeometry(self.left, self.top, self.width, self.height)

        self.fromLangPrompt()
        self.toLangPrompt()
        self.fromBox()
        self.toBox()
        self.translateButton()
        self.audioButton()
        self.googleResults()

    def googleResults(self):
        self.prompt = QLabel('Google Results', self)
        self.prompt.setGeometry(QRect(465,15,300,28))
        self.results = QTextBrowser(self)
        self.results.setOpenExternalLinks(True)
        self.results.setGeometry(QRect(465,50,350,397))

    def fromBox(self):
        self.searchText = QPlainTextEdit(self)
        self.searchText.setGeometry(QRect(50,160,350,150))

    def toBox(self):
        self.translatedText = QPlainTextEdit(self)
        self.translatedText.setGeometry(QRect(50,295,350,150))

    def audioButton(self):
        self.audioBtn = QPushButton("", self)
        self.audioBtn.setIcon(QtGui.QIcon('soundIcon.png'))
        self.audioBtn.setIconSize(QSize(20,20))
        self.audioBtn.clicked.connect(lambda: self.play_sound(self.toLang, self.translatedText.toPlainText()))
        self.audioBtn.resize(40,40)
        self.audioBtn.move(400,290)

    def translateButton(self):
        self.translateBtn = QPushButton("Translate!", self)
        self.translateBtn.resize(100,100)
        self.translateBtn.move(310,32)
        self.translateBtn.clicked.connect(lambda: self.do_translate(self.toLang, awsTranslateCodes[self.fromLang], awsTranslateCodes[self.toLang], self.searchText.toPlainText()))


    def setFromLang(self, index):
        self.fromLang = self.comboBoxF.itemText(index).lower()

    def setToLang(self, index):
        self.toLang = self.comboBoxT.itemText(index).lower()

    def fromLangPrompt(self):
        self.prompt = QLabel('Language to translate from', self)
        self.prompt.setGeometry(QRect(50,15,300,28))
        self.comboBoxF = QComboBox(self)
        self.comboBoxF.setGeometry(QRect(43,50,190,28))

        for key, value in awsTranslateCodes.items():
            self.comboBoxF.addItem(key[:1].upper() + key[1:])

        self.comboBoxF.activated.connect(self.setFromLang)

    def toLangPrompt(self):
        self.prompt = QLabel('Language to translate to', self)
        self.prompt.setGeometry(QRect(50,90, 300,28))
        self.comboBoxT = QComboBox(self)
        self.comboBoxT.setGeometry(QRect(43,125,190,28))

        for key, value in awsTranslateCodes.items():
            self.comboBoxT.addItem(key[:1].upper() + key[1:])

        self.comboBoxT.activated.connect(self.setToLang)

    def do_translate(self, pollyLang, fromLang, toLang, searchText):
        if searchText:
            result = translate.translate_text(Text=searchText,
                      SourceLanguageCode=fromLang, TargetLanguageCode=toLang)
            self.translatedText.clear()
            self.results.clear()
            self.translatedText.setPlainText(result.get("TranslatedText"))
            self.repaint()

            self.google_search(result.get("TranslatedText"))

    def play_sound(self, pollyLang, text):
        pollyCode = ''
        pollyVoice = ''
        print(pollyLang)
        if 'chinese (simplified)' in pollyLang or 'chinese (traditional)' in pollyLang:
            pollyCode = 'cmn-CN'
            pollyVoice = 'Zhiyu'
        elif 'english' in pollyLang:
            pollyCode = 'en-US'
            pollyVoice = 'Matthew'
        elif 'french' in pollyLang:
            pollyCode = 'fr-FR'
            pollyVoice = 'Celine'
        elif 'portuguese' in pollyLang:
            pollyCode = 'pt-BR'
            pollyVoice = 'Ricardo'
        elif 'spanish' in pollyLang:
            pollyCode = 'es-US'
            pollyVoice = 'Lupe'
        else:
            try:
                pollyCode = pollyCodes[pollyLang]
            except KeyError:
                pollyCode = 'en-US'

            try:
                pollyVoice = pollyVoices[pollyLang]
            except KeyError:
                pollyVoice = 'Matthew'
        print(pollyVoice)
        response = polly.synthesize_speech(LanguageCode=pollyCode, VoiceId=pollyVoice, OutputFormat='mp3', Text=text)

        body = response['AudioStream'].read()

        file_name = 'voice.mp3'

        with open(file_name, 'wb') as file:
            file.write(body)
            file.close()

        pygame.mixer.init()
        pygame.mixer.music.load('voice.mp3')

        pygame.mixer.music.play()

        while pygame.mixer.music.get_busy():
            pygame.time.Clock().tick(10)

        time.sleep(0.3)

        os.remove('voice.mp3')

    def google_search(self, text):
        USER_AGENT = "Mozilla/5.0 (Macintosh; Intel Mac OS X 10.14; rv:65.0) Gecko/20100101 Firefox/65.0"
        MOBILE_USER_AGENT = "Mozilla/5.0 (Linux; Android 7.0; SM-G930V Build/NRD90M) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/59.0.3071.125 Mobile Safari/537.36"

        text = text.replace(' ', '+')
        URL = "https://google.com/search?q=" + text

        headers = {"user-agent": USER_AGENT}
        response = requests.get(URL, headers=headers)

        if response.status_code == 200:
            soup = BeautifulSoup(response.content, "html.parser")
            res = []
            for g in soup.find_all('div', class_='r'):
                aTags = g.find_all('a')
                if aTags:
                    link = aTags[0]['href']
                    title = g.find('h3').text
                    item = {
                        "title": title,
                        "link": link
                    }

                    analysis = comprehend.batch_detect_sentiment(TextList=[title], LanguageCode='zh')
                    sentiment = analysis['ResultList'][0]['Sentiment']
                    sentiment = sentiment.lower()
                    sentiment = sentiment[:1].upper() + sentiment[1:]
                    confidence = analysis['ResultList'][0]['SentimentScore']

                    self.results.insertPlainText(title + "\n")
                    self.results.append("<a href=\"" + link + "\"" + ">" + link + "</a>")
                    self.results.insertPlainText("\n")
                    self.results.insertPlainText("Title Sentiment: " + sentiment + "\n")
                    self.results.insertPlainText("Confidence Score: " + str(round(confidence[sentiment], 2) * 100) + "%\n\n")

                    self.repaint()




    # def main():
    #     fromLang = input('What language will you be using?: ').lower()

    #     if fromLang == 'chinese':
    #         langType = input('Simplified or Traditional?: ').lower()
    #         if langType == 'simplified':
    #             fromLang = 'chinese (simplified)'
    #         elif langType == 'Traditional':
    #             fromLang = 'chinese (traditional)'

    #     toLang = input('What language do you want to translate to?: ').lower()

    #     if toLang == 'chinese':
    #         langType = input('Simplified or Traditional?: ').lower()
    #         if langType == 'simplified':
    #             toLang = 'chinese (simplified)'
    #         elif langType == 'traditional': toLang = 'chinese (traditional)'
    #     searchText = input('Enter some text: ')

    #     do_translate(toLang, awsTranslateCodes[fromLang], awsTranslateCodes[toLang], searchText)


if __name__ == "__main__":
    font = QtGui.QFont("Arial", 17)
    App = QApplication(sys.argv)
    App.setFont(font)
    window = Window()
    window.center()
    window.show()
    sys.exit(App.exec_())
