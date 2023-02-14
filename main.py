import tkinter as tk
from tkinter import *
from tkinter import ttk, font, messagebox, filedialog
from PIL import Image, ImageTk
import os, DataBase, time, datetime, threading, pathlib, shutil, PyPDF2
from pyInstalledPath import relpath
from mitra import *

PLOCHA = os.path.normpath(os.path.expanduser("~/Desktop"))

# 0 - neudelal ukol, neotevrel napovedu
# 1 - neudelal ukol, otevrel napovedu
# 2 - udelal ukol, neotevrel napovedu
# 3 - udelal ukol, otevrel napovedu

class Aplikace(tk.Tk):
    def __init__(self):
        super().__init__()
        # Variables
        self.obrazky = []
        self.odevzdanySoubor = ""
        self.ulozenaData = {}
        self.serverKontaktovan = False
        self.napovedaDostupna = False
        self.prvniMitraSoubor = ""
        self.druhyMitraSoubor = ""

        # Od středu monitoru odečte půlku zadaných hodnot, a tim ziská střed. Vrací pro tkinter geometry.
        def center(self, sizeX: int, sizeY: int):
            displayX = self.winfo_screenwidth()
            displayY = self.winfo_screenheight()
            centerX = round((displayX/2) - (sizeX/2))
            centerY = round((displayY/2) - (sizeY/2))
            return str(sizeX) + "x" + str(sizeY) + "+" + str(centerX) + "+" + str(centerY)

        # Otevře obrázek, změnní jeho velikost, a dá na pozici x, y.
        def openImage(self, path: str, sizeX: int, sizeY: int, posX: int, posY: int):
            obrazek = Image.open(path)
            obrazek = obrazek.resize((sizeX, sizeY), Image.ANTIALIAS)
            obrazek = ImageTk.PhotoImage(obrazek)
            self.obrazky.append(Label(self, image=obrazek))
            self.obrazky[-1].image = obrazek
            self.obrazky[-1].place(x= posX, y= posY)

        # Projede list images a zničí všechny.
        def destoyAllImages(self):
            for i in range(len(self.obrazky)):
                self.obrazky[i].destroy()

        # Otevře průzkumník souborů pro výběr souboru, a budou vidě pouze ty, který jsou nastený ve funkci.
        def browseFiles(self, fileformat: str, mode: int):
            soubor = filedialog.askopenfilename(initialdir = PLOCHA,
                                                title =
                                                    "Vyberte soubor",
                                                filetypes =
                                                    ((f"Soubory {fileformat}", f"*.{fileformat}*"),
                                                    (None, None)))
            try:
                # Mód se učruje ve funkci. Každý mód ukládá do jiné proměnné.
                if mode == 1:
                    self.prvniMitraSoubor = soubor
                elif mode == 2:
                    self.druhyMitraSoubor = soubor
                elif mode == 3:
                    self.odevzdanySoubor = soubor
            except NameError:
                pass

        # Spojování se servrem, pokud neuspěje tak po sekundách zadaných ve funkci zkusí znova.
        def kontaktovaniServru(self, seconds: int):
            while True:
                time.sleep(seconds)
                if not self.serverKontaktovan and DataBase.zkontrolovatConfigSoubor():
                    self.serverKontaktovan, self.ulozenaData = DataBase.synchrozovaniServeru(self.ulozenaData)

        # Odpočet nápovědy.
        def napovedaTimer(self, seconds: int):
            time.sleep(seconds)
            self.napovedaDostupna = True

        # Kontrola jestli je už nápověda dostupná.
        def jeNapovedaDostupna(self):
            if self.napovedaDostupna == True:
                messagebox.showinfo(title=
                                        "Nápověda",
                                    message=
                                        "Přípony souborů měň přesně v tom pořadí, jako jsou uvedeny v zadání.\nJakmile se dostaneš k prvnímu zip souboru, tak ho rozbal, a přečti si zadání v něm.\nPokud budeš správně postupovat, získáš dva soubory se zvláštními názvy. Jeden z nich je ten správný, ten odevzdej.")
                if self.ulozenaData["task"] == 0:
                    self.ulozenaData["hint"] = 1
                    DataBase.ulozitConfigSoubor(self.ulozenaData)
                self.serverKontaktovan, self.ulozenaData = DataBase.synchrozovaniServeru(self.ulozenaData)
                rozcestnik(self)
            else:
                messagebox.showerror(title=
                                        "Chyba",
                                    message=
                                        "Nápověda ještě není k dispozici. Pro zobrazení nápovědy musíš počkat 3 minuty od přihlášení. Mezitím zkoušej dál.")
                rozcestnik(self)

        # Kontrola souboru. Jestli soubor jde otevřít přes library tak se jedná o validní pdf čili špatná odpověd. Pokud pdf nejde tak je to správná odpověd.
        def kontrolaOdpovedi(self, file: str):
            try:
                pdfFileObject = open(file, 'rb')
                try:
                    PyPDF2.PdfFileReader(pdfFileObject)
                    messagebox.showerror(title=
                                            "Odevzdání",
                                        message=
                                            "Odevzdaný soubor není správný")

                except Exception:
                    messagebox.showinfo(title=
                                            "Odevzdání",
                                        message=
                                            "Tvé vypracování je správné, skvělá práce!")
                    self.ulozenaData["task"] = 1
                    DataBase.ulozitConfigSoubor(self.ulozenaData)
                    self.serverKontaktovan, self.ulozenaData = DataBase.synchrozovaniServeru(self.ulozenaData)
            except Exception:
                messagebox.showerror(title=
                                        "Odevzdání",
                                    message=
                                        "Nebyl nahrán žádný soubor!")

        # Kontrola přihlášení.
        def prihlaseni(username: str, heslo: str):
            jmeno = username.get()
            heslo = heslo.get()
            if(jmeno == "" or heslo == ""):
                messagebox.showerror(title=
                                        "Chybné přihlašovací údaje",
                                    message=
                                        "Vyplň prosím všechna pole")
            else:
                # Podívání se do databáze pro vrátit jestli tam je jméno a heslo.
                loginSuccess = DataBase.overitPrihlaseni(jmeno, heslo, DataBase.attendee_dict)
                try:
                    if loginSuccess:
                        # Vytvoření config souboru.
                        self.ulozenaData = DataBase.vytvoritConfigSoubor(jmeno, heslo)
                        self.serverKontaktovan, self.ulozenaData = DataBase.synchrozovaniServeru(self.ulozenaData)
                        # Název okna po přihlášení.
                        self.title(f"Purkiáda 2023 - úloha 8 ({self.ulozenaData['username']}; nová relace)")
                        return True
                    else:
                        messagebox.showerror(title=
                                                "Chybné přihlašovací údaje",
                                            message=
                                                "Zkontroluj prosím své přihlašovací údaje")
                        return False
                except Exception as e:
                    messagebox.showerror(title=
                                            "Chyba",
                                        message=
                                            f"Kritická chyba aplikace\nPokud toto vidíš, oznam to prosím pořadatelům soutěže\n\n{e}")
                    return False

        # Mitra, ze dvou zadaných souborů vytvoří polyglot.
        def mitraProcess(self, soubor1, soubor2):
            file1 = soubor1
            file2 = soubor2
            # Chyba - Chybí oba soubory
            if not file1 or not file2:
                messagebox.showerror(title=
                                        "Chyba zpracování souborů",
                                    message=
                                        "Nahraj prosím oba soubory")
                return
            # Otevře první soubor
            with open(file1, "rb") as f:
                fileData1 = f.read()
            # Otevře druhý soubor
            with open(file2, "rb") as f:
                fileData2 = f.read()

            fileData1 += b"\1" * (len(fileData1))
            fileData2 += b"\1" * (len(fileData2))

            fileType1 = None
            fileType2 = None

            for parser in PARSERS:
                fileType = parser.parser
                f = fileType(fileData1)
                if f.identify():
                    fileType1 = f
                f = fileType(fileData2)
                if f.identify():
                    fileType2 = f

            # Chyba - Chybí první soubor.
            if fileType1 is None:
                    messagebox.showerror(title=
                                            "Chyba zpracování souborů",
                                        message=
                                            "Nahrajte prosím i první soubor")
            # Chyba - Chybí druhý soubor.
            elif fileType2 is None:
                    messagebox.showerror(title=
                                            "Chyba zpracování souborů",
                                        message=
                                            "Nahrajte prosím i druhý soubor")
            # Chyba - Oba soubory jsou stejné.
            elif fileType1.TYPE == fileType2.TYPE:
                    messagebox.showerror(title=
                                            "Chyba zpracování souborů",
                                        message=
                                            "Tyto soubory mají tu stejnou příponu")
            else:
                # Mitra
                DoAll(fileType1, fileType2, file1, file2)
                # Úspěšně proběhnula Mitra.
                messagebox.showinfo(title=
                                        "Hotovo",
                                    message=
                                        "Soubory byly úspěšně vytvořeny ve stejné složce, jako je tato úloha.")

        # Vytvoření threadu pro odpočet nápovědy.
        napovedaThread = threading.Thread(target= napovedaTimer, args= (self, 180))
        napovedaThread.start()

        # Vytvoření threadu pro kontrolu připojení se servrem.
        serverThread = threading.Thread(target= kontaktovaniServru, args= (self, 30))
        serverThread.start()

        # Motiv aplikace
        self.tk.call("source", relpath("resources/azure.tcl"))
        self.tk.call("set_theme", "dark")
        # Název okna v příhlášení
        self.title("Purkiáda 2023 - úloha 8")
        # Zakázat resizování okna
        self.resizable(width= False, height= False)
        # Nastavení ikony pro aplikaci
        self.iconbitmap(relpath("resources/purkiada.ico"))

        def okno(self):
            if DataBase.zkontrolovatConfigSoubor():
                try:
                    # Načtení lokálního configu
                    self.ulozenaData = DataBase.nacistConfigSoubor()
                    # Synchronizování se servrem
                    self.serverKontaktovan, self.ulozenaData = DataBase.synchrozovaniServeru(self.ulozenaData)
                    # Název okna po přihlášení
                    self.title(f"Purkiáda 2023 - úloha 8 ({self.ulozenaData['username']}; obnovená relace)")
                except Exception:
                    messagebox.showerror(title=
                                            "Chyba načítání uložených dat",
                                        message=
                                            "Nastala chyba při načítání lokálně uložených dat. Pokud toto vidíš, prosím, oznamte to pořadatelům soutěže.")
                    raise Exception

            if not self.ulozenaData:
                # Velikost okna
                self.geometry(center(self, 300, 205))
                # Nadpis - Příhlášení
                nadpisPrihlaseni = Label(self,
                                        text=
                                            "Přihlášení",
                                        font= ("", 20))
                nadpisPrihlaseni.place(relx= 0.5, y= 25, anchor= "center")
                # Text - Jméno
                jmenoText = Label(self,
                                text=
                                    "Jméno:",
                                font= ("", 10))
                jmenoText.place(x= 60, y= 45)
                # Input - Jméno
                jmenoInput = ttk.Entry(self,
                                    width= 20)
                jmenoInput.place(relx= 0.5, y= 80, anchor= "center")
                # Text - Heslo
                hesloText = Label(self,
                                text=
                                    "Heslo:",
                                font= ("", 10))
                hesloText.place(x= 60, y= 105)
                # Input - Heslo
                hesloInput = ttk.Entry(self,
                                    width= 20,
                                    show= "*")
                hesloInput.place(relx= 0.5, y= 140, anchor= "center")
                # Tlačítko - Přihlásit
                prihlaseniButton = ttk.Button(self,
                                            text=
                                                "Přihlásit",
                                            width= 19,
                                            command=
                                                lambda: [prihlaseni(jmenoInput, hesloInput), nadpisPrihlaseni.destroy(), jmenoText.destroy(), jmenoInput.destroy(), hesloText.destroy(), hesloInput.destroy(), prihlaseniButton.destroy(), rozcestnik(self)] if prihlaseni(jmenoInput, hesloInput) else None)
                prihlaseniButton.place(relx= 0.5, y= 180, anchor= "center")
            else:
                try:
                    rozcestnik(self)
                except Exception as e:
                        messagebox.showerror(title=
                                                "Chyba",
                                            message=
                                                f"Kritická chyba aplikace\nPokud toto vidíte, oznamte to prosím pořadatelům soutěže\n\n{e}")

        def rozcestnik(self):
            # Velikost okna
            self.geometry(center(self, 800, 500))
            # Vytvořit soubor se kterým budou pracovat
            vytvorenySoubor = pathlib.Path(PLOCHA + "\\skolniRad.pdf")
            if not vytvorenySoubor.exists():
                shutil.copy(relpath("resources/skolniRad.pdf"), PLOCHA + "\\skolniRad.pdf")
            else:
                pass
            # Nadpis - Zadání
            zadaniText = Label(self,
                            text=
                                "Zadání:"
                                "\n"
                                "V této úloze budeš měnit připony souborů, aby se ti odhalil nový soubor.\nPřípony jsou například PDF, ZIP, HTML, ...\n\n"
                                "Ve stejné složce, jako je tento program, najdi soubor 'skolníRad.pdf'.\nOpravdu se jedná o PDF, ale není to třeba i něco jiného?\n\n"
                                "Podrobně si přečti zadání a zkus přepsat příponu souboru (návod pro povolení přípon níže).\n"
                                "Pokud si ani tak nebudeš vědět rady, po třech minutách budeš moct použít nápovědu\n(za úspěšné dokončení ale budeš mít o 2 body méně.).",
                            font= ("", 12))
            zadaniText.place(relx= 0.5, y= 90, anchor= "center")
            # Tlačítko - Jak povolit připony souborů
            jakPovolitPriponySouboruButton = ttk.Button(self,
                                                        text=
                                                            "Jak povolit připony souborů",
                                                        width= 40,
                                                        command=
                                                            lambda: [zadaniText.destroy(), jakPovolitPriponySouboruButton.destroy(), odevzdaniButton.destroy(), napovedaButton.destroy(), mitraButton.destroy(), vyvojariButton.destroy(), progressText.destroy(), povoleniPripon(self)])
            jakPovolitPriponySouboruButton.place(relx= 0.5, y= 220, anchor= "center", height= 35)
            # Tlačítko -Mitra
            mitraButton = ttk.Button(self,
                                    text=
                                        "Mitra",
                                    width= 40,
                                    command=
                                        lambda: [zadaniText.destroy(), jakPovolitPriponySouboruButton.destroy(), odevzdaniButton.destroy(), napovedaButton.destroy(), mitraButton.destroy(), vyvojariButton.destroy(), progressText.destroy(), mitra(self)])
            mitraButton.place(relx= 0.5, y= 265, anchor= "center", height= 35)
            # Tlačítko - Odevzdání
            odevzdaniButton = ttk.Button(self,
                                        text=
                                            "Odevzdání",
                                        width= 40,
                                        command=lambda:
                                            [zadaniText.destroy(), jakPovolitPriponySouboruButton.destroy(), odevzdaniButton.destroy(), napovedaButton.destroy(), mitraButton.destroy(), vyvojariButton.destroy(), progressText.destroy(), odevzdani(self)])
            odevzdaniButton.place(relx= 0.5, y= 310, anchor= "center", height= 35)
            # Tlačítko - Nápověda
            napovedaButton = ttk.Button(self,
                                        text=
                                            "Nápověda",
                                        width= 40,
                                        command=
                                            lambda: [zadaniText.destroy(), jakPovolitPriponySouboruButton.destroy(), odevzdaniButton.destroy(), napovedaButton.destroy(), mitraButton.destroy(), vyvojariButton.destroy(), progressText.destroy(), jeNapovedaDostupna(self)])
            napovedaButton.place(relx= 0.5, y= 355, anchor= "center", height= 35)
            # Tlačítko - Vývojáři
            vyvojariButton = ttk.Button(self,
                                        text=
                                            "Vývojáři",
                                        width= 40,
                                        command=
                                            lambda: [zadaniText.destroy(), jakPovolitPriponySouboruButton.destroy(), odevzdaniButton.destroy(), napovedaButton.destroy(), mitraButton.destroy(), vyvojariButton.destroy(), progressText.destroy(), vyvojari(self)])
            vyvojariButton.place(relx= 0.5, y= 400, anchor= "center", height= 35)
            # Nadpis - Progress
            progressText = Label(self,
                                text=
                                    f"Úkol {'byl správně' if self.ulozenaData['task'] else 'nebyl'} vypracován, "
                                    f"nápověda {'byla' if self.ulozenaData['hint'] else 'nebyla'} zobrazena\n"
                                    f"Celkový počet bodů: {(5 if self.ulozenaData['task'] else 0) + (0 if self.ulozenaData['hint'] else (2 if self.ulozenaData['task'] else 0))} b\n"
                                    f"Postup se ukládá na server: {'ANO' if self.serverKontaktovan else 'NE'}",
                                font= ("", 12))
            progressText.place(relx= 0.5, y= 465, anchor= "center")

        def povoleniPripon(self):
            # Velikost okna
            self.geometry(center(self, 1280, 500))
            # Nadpis - První krok
            prvniKrokPopis = Label(self,
                                text=
                                    "1. Otevři průzkumník souborů",
                                font= ("", 14))
            prvniKrokPopis.place(x= 20, y= 60)
            # Načtení obrázku s prvním krokem
            prvniKrokObrazek = openImage(self, relpath("resources/img/krok1.png"), 400, 200, 20, 90)
            # Nadpis - Druhý krok
            druhyKrokPopis = Label(self,
                                text=
                                    "2. Nahoře klikni na zobrazení",
                                font= ("", 14))
            druhyKrokPopis.place(x= 440, y= 160)
            # Načtení obrázku s druhým krokem
            druhyKrokObrazek = openImage(self, relpath("resources/img/krok2.png"), 400, 200, 440, 190)
            # Nadpis - Třetí krok
            tretiKrokPopis = Label(self,
                                text=
                                    "3. Zaškrtni přípony názvů souborů",
                                font= ("", 14))
            tretiKrokPopis.place(x= 860, y= 60)
            # Načtení obrázku s třetím krokem
            tretiKrokObrazek = openImage(self, relpath("resources/img/krok3.png"), 400, 200, 860, 90)
            # Tlačítko - Rozcestník
            rozcestnikButton = ttk.Button(self,
                                        text=
                                            "Zpět na rozcestník",
                                        width= 20,
                                        command=
                                            lambda: [rozcestnikButton.destroy(), prvniKrokPopis.destroy(), druhyKrokPopis.destroy(), tretiKrokPopis.destroy(), destoyAllImages(self), rozcestnik(self)])
            rozcestnikButton.place(relx= 0.5, y= 475, anchor= "center")

        def mitra(self):
            # Velikost okna
            self.geometry(center(self, 800, 500))
            # Nadpis - Popis Mitry
            mitraPopisText = Label(self,
                                text=
                                    "Mitra je nástroj na generování binárních polyglotů\n(to jsou soubory, které jsou platné s několika formáty souborů)\n",
                                font= ("", 12))
            mitraPopisText.place(relx= 0.5, y= 130, anchor= "center")
            # Text - Path k prvnímu souboru
            prvniSouborPath = Label(self,
                                    text =
                                        "",
                                    font= ("", 9), bg= "#868353")
            prvniSouborPath.place(relx= 0.5, y= 205, anchor= "center")
            # Tlačítko - Vybrat prnví soubor
            prvniSouborButton = ttk.Button(self,
                                        text=
                                            "Vybrat první soubor (PDF)",
                                        width= 25,
                                        command=
                                            lambda: [browseFiles(self, "pdf", 1), prvniSouborPath.configure(text= self.prvniMitraSoubor)])
            prvniSouborButton.place(relx= 0.5, y= 170, anchor= "center")
            # Text - Path k druhému souboru
            druhySouborPath = Label(self,
                            text =
                                "",
                            font= ("", 9), bg= "#868353")
            druhySouborPath.place(relx= 0.5, y= 275, anchor= "center")
            # Tlačítko - Vybrat druhý soubor
            druhySouborButton = ttk.Button(self,
                                        text=
                                            "Vybrat druhý soubor (ZIP)",
                                        width= 25,
                                        command=
                                            lambda: [browseFiles(self, "zip", 2), druhySouborPath.configure(text= self.druhyMitraSoubor)])
            druhySouborButton.place(relx= 0.5, y= 240, anchor= "center")
            # Tlačítko - Start
            mitraStartButton = ttk.Button(self,
                                        text=
                                            "Start!",
                                        width= 20,
                                        command=
                                            lambda: [mitraProcess(self, self.prvniMitraSoubor, self.druhyMitraSoubor)])
            mitraStartButton.place(relx= 0.5, y= 310, anchor= "center")
            # Tlačítko - Rozcestník
            rozcestnikButton = ttk.Button(self,
                                        text=
                                            "Zpět na rozcestník",
                                        width= 20,
                                        command=
                                            lambda:[mitraPopisText.destroy(), prvniSouborButton.destroy(), prvniSouborPath.destroy(), druhySouborButton.destroy(), druhySouborPath.destroy(), mitraStartButton.destroy(), rozcestnikButton.destroy(), rozcestnik(self)])
            rozcestnikButton.place(relx= 0.5, y= 350, anchor= "center")

        def odevzdani(self):
            # Velikost okna
            self.geometry(center(self, 800, 500))
            # Nadpis
            odevzdaniText = Label(self,
                                text=
                                    "Nahraj PDF soubor, který jsi vytvořil/a nástrojem Mitra",
                                font= ("", 12))
            odevzdaniText.place(relx= 0.5, y= 120, anchor= "center")
            # Text - Path vybraného souboru
            vybranySouborPath = Label(self,
                                    text =
                                        "",
                                    font= ("", 9), bg= "#868353")
            vybranySouborPath.place(relx= 0.5, y= 235, anchor= "center")
            # Tlačítko - Vybrat soubor
            vybratSouborButton = ttk.Button(self,
                                            text=
                                                "Vybrat soubor (PDF)",
                                            width= 25,
                                            command=
                                                lambda: [browseFiles(self, "pdf", 3), vybranySouborPath.configure(text= self.odevzdanySoubor)])
            vybratSouborButton.place(relx= 0.5, y= 175, anchor= "center")
            # Tlačítko - Odevzdat
            odevzdaniButton = ttk.Button(self,
                                        text="Odevzdat",
                                        width= 20,
                                        command=
                                            lambda: [kontrolaOdpovedi(self, self.odevzdanySoubor)])
            odevzdaniButton.place(relx= 0.5, y= 310, anchor= "center")
            # Tlačítko - Rozcestník
            rozcestnikButton = ttk.Button(self,
                                        text="Zpět na rozcestník",
                                        width= 20,
                                        command=
                                            lambda: [odevzdaniText.destroy(), vybratSouborButton.destroy(), vybranySouborPath.destroy(), odevzdaniButton.destroy(), rozcestnikButton.destroy(), rozcestnik(self)])
            rozcestnikButton.place(relx= 0.5, y= 350, anchor= "center")

        def vyvojari(self):
            # Velikost okna
            self.geometry(center(self, 410, 280))
            # Nadpis
            vyvojariText = Label(self,
                                text=
                                    "Vývojáři:"
                                    "\n\n"
                                    "Karol Raffay\n"
                                    "Ondrej Dítě"
                                    "\n\n"
                                    "Vytvořeno pro Purkiádu, ročník 2023.",
                                font= ("", 12))
            vyvojariText.place(relx= 0.5, y= 80, anchor= "center")
            # Tlačítko - Rozcestník
            rozcestnikButton = ttk.Button(self,
                                        text=
                                            "Zpět na rozcestník",
                                        width= 20,
                                        command=
                                            lambda: [vyvojariText.destroy(), rozcestnikButton.destroy(), rozcestnik(self)])
            rozcestnikButton.place(relx= 0.5, y= 250, anchor= "center")

        okno(self)

Aplikace().mainloop()
os._exit(0)
