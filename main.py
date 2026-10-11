import math
import os
import sqlite3
import sys
from datetime import datetime, date as dt_date
from pathlib import Path

from kivy.config import Config
from kivy.utils import platform

# Sur PC : fenetre au format "telephone" comme la maquette (inutile sur Android)
if platform != "android":
    Config.set("graphics", "width", "432")
    Config.set("graphics", "height", "700")
    Config.set("graphics", "minimum_width", "340")
    Config.set("graphics", "minimum_height", "520")

from kivy.core.window import Window
from kivy.app import App
from kivy.lang import Builder
from kivy.metrics import dp
from kivy.animation import Animation
from kivy.clock import Clock
from kivy.factory import Factory
from kivy.properties import (StringProperty, ListProperty, NumericProperty,
                             BooleanProperty)
from kivy.uix.behaviors import ButtonBehavior
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.image import Image
from kivy.uix.label import Label
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.scrollview import ScrollView
from kivy.uix.textinput import TextInput
from kivy.uix.spinner import Spinner  # noqa: F401
from kivy.uix.widget import Widget
from kivy.uix.floatlayout import FloatLayout
from kivy.uix.gridlayout import GridLayout
from kivy.graphics import Color, Ellipse, Rectangle

Window.clearcolor = (.95, .96, .98, 1)
if platform == "android":
    # Le clavier ne doit pas cacher le champ en cours de saisie
    Window.softinput_mode = "below_target"


def _base_dir():
    return getattr(sys, "_MEIPASS", None) or os.path.dirname(os.path.abspath(__file__))


ASSETS = os.path.join(_base_dir(), "assets").replace("\\", "/")


def asset(name):
    return f"{ASSETS}/{name}.png"


DEFAULT_BUDGET = [
    ("logement", "Logement", 25),
    ("alimentation", "Alimentation", 25),
    ("famille", "Enfants / famille", 8),
    ("transport", "Transport", 5),
    ("eau", "Eau / électricité / gaz", 5),
    ("communication", "Communication", 3),
    ("sante", "Santé / imprévus", 4),
    ("parents", "Aide aux parents", 5),
    ("dime", "Dîme", 10),
    ("epargne", "Épargne", 5),
    ("projets", "Projets / autres", 5),
]

SCREEN_PARENTS = {
    "food": "budget",
    "shopping": "expenses",
    "savings_history": "savings",
    "savings_details": "savings",
    "goal_detail": "goals",
}

FOOD_DEFAULT = [
    ("f_riz", "Sac de riz 50 kg", 20000),
    ("f_viande", "Viande / poisson", 20000),
    ("f_legumes", "Légumes / condiments", 15000),
    ("f_pain", "Pain / petit-déjeuner", 10000),
    ("f_autres", "Autres aliments", 10000),
]

KV = r"""
#:import dp kivy.metrics.dp

<Label>:
    color: .10,.18,.27,1

<Button>:
    background_normal: ""
    background_down: ""
    background_color: .88,.91,.95,1
    color: .06,.20,.36,1
    bold: True
    opacity: .8 if self.state == "down" else 1

<TextInput>:
    background_normal: ""
    background_active: ""
    background_color: 1,1,1,1
    foreground_color: .10,.18,.27,1
    hint_text_color: .55,.60,.66,1
    cursor_color: .04,.30,.55,1
    padding: [dp(10), dp(12)]
    canvas.after:
        Color:
            rgba: .76,.81,.87,1
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(8)
            width: 1

<Popup>:
    background: ""
    background_color: 1,1,1,1
    title_color: .04,.20,.38,1
    separator_color: .03,.55,.30,1

<PrimaryButton@Button>:
    size_hint_y: None
    height: dp(50)
    background_color: .03,.55,.30,1
    color: 1,1,1,1

<DangerButton@Button>:
    size_hint_y: None
    height: dp(44)
    background_color: 1,.91,.91,1
    color: .70,.08,.08,1

<Header@BoxLayout>:
    size_hint_y: None
    height: dp(58)
    padding: dp(7), 0
    canvas.before:
        Color:
            rgba: .04,.20,.38,1
        Rectangle:
            pos: self.pos
            size: self.size
    MenuButton:
        on_release: app.open_menu()
    Label:
        text: "MON SALAIRE"
        font_size: "22sp"
        bold: True
        color: 1,1,1,1
    Widget:
        size_hint_x: None
        width: dp(44)

<MenuButton>:
    size_hint_x: None
    width: dp(44)
    canvas:
        Color:
            rgba: (1,1,1,.55) if self.state == "down" else (1,1,1,1)
        Rectangle:
            pos: self.center_x - dp(13), self.center_y + dp(7)
            size: dp(26), dp(3)
        Rectangle:
            pos: self.center_x - dp(13), self.center_y - dp(1.5)
            size: dp(26), dp(3)
        Rectangle:
            pos: self.center_x - dp(13), self.center_y - dp(10)
            size: dp(26), dp(3)

<Drawer@BoxLayout>:
    canvas.before:
        Color:
            rgba: 1,1,1,1
        Rectangle:
            pos: self.pos
            size: self.size

<DrawerHead@BoxLayout>:
    canvas.before:
        Color:
            rgba: .04,.20,.38,1
        Rectangle:
            pos: self.pos
            size: self.size

<MenuItem>:
    size_hint_y: None
    height: dp(50)
    padding: dp(16), dp(6)
    spacing: dp(14)
    canvas.before:
        Color:
            rgba: (.90,.94,.98,1) if (self.state == "down" or self.active) else (1,1,1,1)
        Rectangle:
            pos: self.pos
            size: self.size
    Image:
        source: root.source
        size_hint_x: None
        width: dp(34)
        fit_mode: "contain"
    Label:
        text: root.text
        font_size: "15sp"
        bold: True
        halign: "left"
        valign: "middle"
        text_size: self.size
        color: root.fg

<ResetScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Remise à zéro"
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                id: content
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height

<TopBar>:
    size_hint_y: None
    height: dp(56)
    padding: dp(6), 0
    canvas.before:
        Color:
            rgba: .04,.20,.38,1
        Rectangle:
            pos: self.pos
            size: self.size
    Button:
        text: "‹"
        font_size: "36sp"
        size_hint_x: None
        width: dp(48)
        background_color: 0,0,0,0
        color: 1,1,1,1
        on_release: app.sm.current = root.back
    Label:
        text: root.title
        font_size: "20sp"
        bold: True
        color: 1,1,1,1
    Widget:
        size_hint_x: None
        width: dp(48)

<StatCard>:
    orientation: "vertical"
    padding: dp(4)
    canvas.before:
        Color:
            rgba: root.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
    Label:
        text: root.title
        font_size: "13sp"
        color: root.fg
    Label:
        text: root.value
        font_size: "17sp"
        bold: True
        color: root.fg

<IconTile>:
    orientation: "vertical"
    size_hint_y: None
    height: dp(108)
    padding: dp(6)
    opacity: .75 if self.state == "down" else 1
    canvas.before:
        Color:
            rgba: 1,1,1,1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
        Color:
            rgba: .86,.89,.93,1
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(14)
            width: 1
    Image:
        source: root.source
        fit_mode: "contain"
    Label:
        text: root.text
        size_hint_y: None
        height: dp(34)
        font_size: "13sp"
        bold: True
        halign: "center"
        valign: "middle"
        text_size: self.size

<RowButton>:
    size_hint_y: None
    height: dp(64)
    padding: dp(10), dp(6)
    spacing: dp(12)
    opacity: .75 if self.state == "down" else 1
    canvas.before:
        Color:
            rgba: 1,1,1,1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
        Color:
            rgba: .86,.89,.93,1
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(14)
            width: 1
    Image:
        source: root.source
        size_hint_x: None
        width: dp(64)
        fit_mode: "contain"
    Label:
        text: root.text
        font_size: "15sp"
        bold: True
        halign: "left"
        valign: "middle"
        text_size: self.size
    Label:
        text: "›"
        font_size: "26sp"
        size_hint_x: None
        width: dp(24)

<RowCard>:
    size_hint_y: None
    height: dp(60)
    padding: dp(8), dp(4)
    spacing: dp(6)
    canvas.before:
        Color:
            rgba: 1,1,1,1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(10)]
        Color:
            rgba: .88,.91,.94,1
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(10)
            width: 1

<ChartCard>:
    orientation: "vertical"
    size_hint_y: None
    height: self.minimum_height
    padding: dp(12)
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: 1,1,1,1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
        Color:
            rgba: .86,.89,.93,1
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(14)
            width: 1

<HBar>:
    canvas:
        Color:
            rgba: .90,.92,.95,1
        RoundedRectangle:
            pos: self.x, self.center_y - dp(7)
            size: self.width, dp(14)
            radius: [dp(7)]
        Color:
            rgba: root.color
        RoundedRectangle:
            pos: self.x, self.center_y - dp(7)
            size: (max(self.width * root.fraction, dp(8)) if root.fraction > 0 else 0), dp(14)
            radius: [dp(7)]

<VBar>:
    canvas:
        Color:
            rgba: root.color
        RoundedRectangle:
            pos: self.x + dp(8), self.y
            size: self.width - dp(16), max(self.height * root.fraction, dp(4))
            radius: [dp(6)]

<Dot>:
    size_hint: None, None
    size: dp(12), dp(12)
    pos_hint: {"center_y": .5}
    canvas:
        Color:
            rgba: root.color
        Ellipse:
            pos: self.pos
            size: self.size

<ReportsScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Rapports"
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                id: content
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height

<FieldLabel@Label>:
    size_hint_y: None
    height: dp(20)
    font_size: "12sp"
    bold: True
    color: .45,.50,.56,1
    halign: "left"
    valign: "middle"
    text_size: self.size

<Tag>:
    size_hint: None, None
    size: self.texture_size[0] + dp(18), dp(22)
    font_size: "11sp"
    bold: True
    color: self.fg
    canvas.before:
        Color:
            rgba: self.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(11)]

<HeroCard>:
    padding: dp(14)
    spacing: dp(12)
    canvas.before:
        Color:
            rgba: root.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(18)]

<StatIcon>:
    size_hint_y: None
    height: dp(64)
    padding: dp(8)
    spacing: dp(8)
    canvas.before:
        Color:
            rgba: root.bg
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
    Image:
        source: root.source
        size_hint_x: None
        width: dp(36)
        fit_mode: "contain"
    BoxLayout:
        orientation: "vertical"
        Label:
            text: root.title
            font_size: "11sp"
            halign: "left"
            valign: "middle"
            text_size: self.size
            color: root.fg
        Label:
            text: root.value
            font_size: "16sp"
            bold: True
            halign: "left"
            valign: "middle"
            text_size: self.size
            color: root.fg

<ActionTile>:
    size_hint_y: None
    height: dp(62)
    padding: dp(8)
    spacing: dp(8)
    opacity: .75 if self.state == "down" else 1
    canvas.before:
        Color:
            rgba: 1,1,1,1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
        Color:
            rgba: .86,.89,.93,1
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(12)
            width: 1
    Image:
        source: root.source
        size_hint_x: None
        width: dp(46)
        fit_mode: "contain"
    Label:
        text: root.text
        font_size: "13sp"
        bold: True
        halign: "left"
        valign: "middle"
        text_size: self.size

<GoalRow>:
    size_hint_y: None
    padding: dp(8)
    spacing: dp(10)
    opacity: .75 if self.state == "down" else 1
    canvas.before:
        Color:
            rgba: 1,1,1,1
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(14)]
        Color:
            rgba: .86,.89,.93,1
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(14)
            width: 1

<IconPick>:
    orientation: "vertical"
    padding: dp(3)
    opacity: .75 if self.state == "down" else 1
    canvas.before:
        Color:
            rgba: (.03,.55,.30,1) if root.selected else (.86,.89,.93,1)
        RoundedRectangle:
            pos: self.pos
            size: self.size
            radius: [dp(12)]
        Color:
            rgba: 1,1,1,1
        RoundedRectangle:
            pos: self.x + dp(2), self.y + dp(2)
            size: self.width - dp(4), self.height - dp(4)
            radius: [dp(10)]
    Image:
        source: root.source
        fit_mode: "contain"
    Label:
        text: root.text
        size_hint_y: None
        height: dp(16)
        font_size: "10sp"
        bold: root.selected

<SegButton>:
    background_color: self.act_color if self.active else (.88,.91,.95,1)
    color: (1,1,1,1) if self.active else (.06,.20,.36,1)

<Spinner>:
    background_color: 1,1,1,1
    color: .10,.18,.27,1
    padding: dp(12), 0, dp(36), 0
    halign: "left"
    valign: "middle"
    text_size: self.size
    canvas.after:
        Color:
            rgba: .76,.81,.87,1
        Line:
            rounded_rectangle: self.x, self.y, self.width, self.height, dp(8)
            width: 1
        Color:
            rgba: .04,.30,.55,1
        Triangle:
            points: self.right - dp(28), self.center_y + dp(4), self.right - dp(14), self.center_y + dp(4), self.right - dp(21), self.center_y - dp(5)

<SavingsScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Épargne"
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                id: content
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height

<SavingsHistoryScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Historique de l'épargne"
            back: "savings"
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                id: content
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height

<SavingsDetailsScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Détails de l'épargne"
            back: "savings"
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                id: content
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height

<GoalsScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Objectifs"
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                id: content
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height

<GoalDetailScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Mon objectif"
            back: root.back_to
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                id: content
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(12)
                size_hint_y: None
                height: self.minimum_height

<AddSavingScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Ajouter une épargne"
            back: root.back_to
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                padding: dp(14)
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height
                BoxLayout:
                    size_hint_y: None
                    height: dp(46)
                    spacing: dp(8)
                    SegButton:
                        text: "Versement"
                        active: root.kind == "in"
                        act_color: .09,.58,.34,1
                        on_release: root.set_kind("in")
                    SegButton:
                        text: "Retrait"
                        active: root.kind == "out"
                        act_color: .85,.25,.25,1
                        on_release: root.set_kind("out")
                FieldLabel:
                    text: "Montant"
                TextInput:
                    id: amount
                    hint_text: "Montant (FCFA)"
                    input_filter: "float"
                    multiline: False
                    font_size: "20sp"
                    size_hint_y: None
                    height: dp(52)
                FieldLabel:
                    text: "Destiné à"
                Spinner:
                    id: goal
                    text: "Épargne libre"
                    size_hint_y: None
                    height: dp(48)
                    on_text: root.update_info()
                Label:
                    text: root.info
                    font_size: "12sp"
                    color: .04,.32,.62,1
                    halign: "left"
                    valign: "middle"
                    text_size: self.width, None
                    size_hint_y: None
                    height: max(dp(22), self.texture_size[1] + dp(4))
                FieldLabel:
                    text: "Date"
                TextInput:
                    id: date
                    hint_text: "JJ-MM-AAAA"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                FieldLabel:
                    text: "Source / note (facultatif)"
                TextInput:
                    id: note
                    hint_text: "Ex : salaire, prime, vente..."
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                PrimaryButton:
                    text: "Enregistrer"
                    on_release: root.save()

<NewGoalScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: root.title_text
            back: root.back_to
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                padding: dp(14)
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height
                FieldLabel:
                    text: "Type de projet"
                BoxLayout:
                    id: icons
                    size_hint_y: None
                    height: dp(78)
                    spacing: dp(6)
                FieldLabel:
                    text: "Nom du projet"
                TextInput:
                    id: name
                    hint_text: "Ex : Maison"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                FieldLabel:
                    text: "Description (facultatif)"
                TextInput:
                    id: note
                    hint_text: "Ex : Achat / construction"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                FieldLabel:
                    text: "Montant cible"
                TextInput:
                    id: target
                    hint_text: "Montant à atteindre (FCFA)"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                FieldLabel:
                    text: "Date souhaitée"
                TextInput:
                    id: due
                    hint_text: "JJ-MM-AAAA (facultatif)"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                FieldLabel:
                    text: "Épargne mensuelle prévue pour ce projet"
                TextInput:
                    id: monthly
                    hint_text: "Ex : 20000 (facultatif)"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                FieldLabel:
                    text: "Priorité"
                BoxLayout:
                    size_hint_y: None
                    height: dp(46)
                    spacing: dp(6)
                    SegButton:
                        text: "Urgente"
                        active: root.priority == "Urgente"
                        act_color: .95,.55,.10,1
                        on_release: root.priority = "Urgente"
                    SegButton:
                        text: "Normale"
                        active: root.priority == "Normale"
                        act_color: .10,.45,.85,1
                        on_release: root.priority = "Normale"
                    SegButton:
                        text: "Secondaire"
                        active: root.priority == "Secondaire"
                        act_color: .55,.30,.85,1
                        on_release: root.priority = "Secondaire"
                PrimaryButton:
                    text: "Enregistrer l'objectif"
                    on_release: root.save()

<StartupScreen>:
    BoxLayout:
        orientation: "vertical"
        padding: dp(24)
        spacing: dp(12)
        Widget:
            size_hint_y: .2
        Image:
            source: "@@/app_icon.png"
            size_hint_y: None
            height: dp(150)
            fit_mode: "contain"
        Label:
            text: "MON SALAIRE"
            font_size: "29sp"
            bold: True
            color: .03,.30,.17,1
            size_hint_y: None
            height: dp(45)
        Label:
            id: status
            text: "Démarrage sécurisé..."
            font_size: "17sp"
            size_hint_y: None
            height: dp(40)
        Label:
            id: checks
            text: ""
            halign: "left"
            valign: "top"
            text_size: self.width, None
            size_hint_y: None
            height: self.texture_size[1]
        Widget:
        PrimaryButton:
            id: retry
            text: "Réessayer"
            disabled: True
            on_release: app.startup()

<HomeScreen>:
    BoxLayout:
        orientation: "vertical"
        Header:
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(10)
                size_hint_y: None
                height: self.minimum_height

                BoxLayout:
                    size_hint_y: None
                    height: dp(122)
                    padding: dp(14)
                    spacing: dp(12)
                    canvas.before:
                        Color:
                            rgba: .09,.58,.34,1
                        RoundedRectangle:
                            pos: self.pos
                            size: self.size
                            radius: [dp(18)]
                    Image:
                        source: "@@/wallet.png"
                        size_hint_x: None
                        width: dp(78)
                        fit_mode: "contain"
                    BoxLayout:
                        orientation: "vertical"
                        Label:
                            text: "Salaire net"
                            color: 1,1,1,1
                            font_size: "16sp"
                            halign: "left"
                            valign: "middle"
                            text_size: self.size
                        Label:
                            text: root.salary_text
                            color: 1,1,1,1
                            font_size: "33sp"
                            bold: True
                            halign: "left"
                            valign: "middle"
                            text_size: self.size
                        Label:
                            text: "Ma famille • Mon budget • Mon avenir"
                            color: .90,1,.94,1
                            font_size: "12sp"
                            halign: "left"
                            valign: "middle"
                            text_size: self.size

                BoxLayout:
                    size_hint_y: None
                    height: dp(70)
                    spacing: dp(10)
                    StatCard:
                        title: "Dépenses"
                        value: root.expenses_text
                        bg: .99,.91,.91,1
                        fg: .70,.08,.08,1
                    StatCard:
                        title: "Épargne"
                        value: root.savings_text
                        bg: .89,.98,.92,1
                        fg: .02,.45,.18,1
                    StatCard:
                        title: "Reste"
                        value: root.remaining_text
                        bg: .88,.94,1,1
                        fg: .04,.32,.62,1

                GridLayout:
                    cols: 3
                    spacing: dp(10)
                    size_hint_y: None
                    height: self.minimum_height
                    IconTile:
                        source: "@@/h_budget.png"
                        text: "Budget\nmensuel"
                        on_release: root.go("budget")
                    IconTile:
                        source: "@@/h_mois.png"
                        text: "13e mois"
                        on_release: root.go("bonus")
                    IconTile:
                        source: "@@/h_dep.png"
                        text: "Dépenses"
                        on_release: root.go("expenses")
                    IconTile:
                        source: "@@/h_epargne.png"
                        text: "Épargne"
                        on_release: root.go("savings")
                    IconTile:
                        source: "@@/h_obj.png"
                        text: "Objectifs"
                        on_release: root.go("goals")
                    IconTile:
                        source: "@@/h_rapport.png"
                        text: "Rapports"
                        on_release: root.go("reports")

                RowButton:
                    source: "@@/cat_famille.png"
                    text: "Scolarité / prêts"
                    on_release: root.go("commitments")

                PrimaryButton:
                    text: "Saisir / modifier mon salaire net"
                    on_release: root.go("salary")

                Label:
                    text: "Le 13e mois est géré séparément du salaire mensuel."
                    color: .45,.50,.56,1
                    font_size: "12sp"
                    size_hint_y: None
                    height: dp(30)

<SalaryScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Salaire net"
        BoxLayout:
            orientation: "vertical"
            padding: dp(14)
            spacing: dp(10)
            Image:
                source: "@@/wallet.png"
                size_hint_y: None
                height: dp(90)
                fit_mode: "contain"
            TextInput:
                id: salary
                hint_text: "Exemple : 300000"
                input_filter: "float"
                multiline: False
                font_size: "22sp"
                size_hint_y: None
                height: dp(54)
            Label:
                text: "Montant réellement reçu en fin de mois."
                color: .45,.50,.56,1
                size_hint_y: None
                height: dp(30)
            PrimaryButton:
                text: "Enregistrer"
                on_release: root.save()
            DangerButton:
                text: "Remettre le salaire à zéro"
                on_release: app.ask_reset("salary", root.on_enter)
            Label:
                text: root.preview
                halign: "left"
                valign: "top"
                text_size: self.width, None

<BudgetScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Budget mensuel"
        ScrollView:
            do_scroll_x: False
            GridLayout:
                id: rows
                cols: 1
                spacing: dp(6)
                padding: dp(10)
                size_hint_y: None
                height: self.minimum_height
        BoxLayout:
            size_hint_y: None
            height: dp(44)
            padding: dp(16), dp(4)
            canvas.before:
                Color:
                    rgba: .84,.95,.88,1
                Rectangle:
                    pos: self.pos
                    size: self.size
            Label:
                text: root.total_text
                bold: True
                color: .03,.40,.22,1
                halign: "left"
                valign: "middle"
                text_size: self.size
        BoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: dp(126)
            padding: dp(10)
            spacing: dp(6)
            PrimaryButton:
                text: "Enregistrer les pourcentages"
                on_release: root.save()
            DangerButton:
                text: "Rétablir les pourcentages par défaut"
                on_release: app.ask_reset("budget_pct", root.on_enter)

<FoodScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Détail alimentation"
            back: "budget"
        BoxLayout:
            size_hint_y: None
            height: dp(96)
            padding: dp(12)
            spacing: dp(12)
            canvas.before:
                Color:
                    rgba: 1,.93,.86,1
                RoundedRectangle:
                    pos: self.x + dp(10), self.y + dp(6)
                    size: self.width - dp(20), self.height - dp(12)
                    radius: [dp(14)]
            Image:
                source: "@@/cat_alimentation.png"
                size_hint_x: None
                width: dp(96)
                fit_mode: "contain"
            BoxLayout:
                orientation: "vertical"
                Label:
                    text: "Budget alimentation"
                    font_size: "14sp"
                    bold: True
                    halign: "left"
                    valign: "middle"
                    text_size: self.size
                Label:
                    text: root.total_text
                    font_size: "24sp"
                    bold: True
                    halign: "left"
                    valign: "middle"
                    text_size: self.size
        ScrollView:
            do_scroll_x: False
            GridLayout:
                id: food_rows
                cols: 1
                spacing: dp(6)
                padding: dp(10)
                size_hint_y: None
                height: self.minimum_height
        BoxLayout:
            orientation: "vertical"
            size_hint_y: None
            height: dp(126)
            padding: dp(10)
            spacing: dp(6)
            PrimaryButton:
                text: "Enregistrer le budget alimentation"
                on_release: root.save()
            DangerButton:
                text: "Rétablir les montants par défaut"
                on_release: app.ask_reset("food", root.on_enter)

<ShoppingScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Courses"
            back: "expenses"
        BoxLayout:
            orientation: "vertical"
            padding: dp(12)
            spacing: dp(8)
            Spinner:
                id: cat
                text: "Alimentation"
                size_hint_y: None
                height: dp(44)
                on_text: root.refresh()
            BoxLayout:
                orientation: "vertical"
                size_hint_y: None
                height: dp(104)
                padding: dp(12), dp(6)
                canvas.before:
                    Color:
                        rgba: 1,1,1,1
                    RoundedRectangle:
                        pos: self.pos
                        size: self.size
                        radius: [dp(12)]
                Label:
                    id: line1
                    text: ""
                    font_size: "13sp"
                    halign: "left"
                    valign: "middle"
                    text_size: self.size
                Label:
                    id: remain
                    text: ""
                    font_size: "20sp"
                    bold: True
                    halign: "left"
                    valign: "middle"
                    text_size: self.size
                HBar:
                    id: bar
                    size_hint_y: None
                    height: dp(12)
            BoxLayout:
                size_hint_y: None
                height: dp(46)
                spacing: dp(6)
                TextInput:
                    id: name
                    hint_text: "Article"
                    multiline: False
                    size_hint_x: .5
                TextInput:
                    id: price
                    hint_text: "Prix"
                    input_filter: "float"
                    multiline: False
                    size_hint_x: .3
                TextInput:
                    id: qty
                    hint_text: "Qté"
                    text: "1"
                    input_filter: "int"
                    multiline: False
                    size_hint_x: .2
            PrimaryButton:
                text: "Ajouter au panier"
                on_release: root.add()
            ScrollView:
                GridLayout:
                    id: cart
                    cols: 1
                    spacing: dp(6)
                    size_hint_y: None
                    height: self.minimum_height
            BoxLayout:
                size_hint_y: None
                height: dp(48)
                spacing: dp(8)
                DangerButton:
                    text: "Vider"
                    size_hint_x: .3
                    on_release: root.clear_cart()
                PrimaryButton:
                    text: "Valider les achats"
                    on_release: root.validate()

<ExpensesScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Dépenses"
        BoxLayout:
            orientation: "vertical"
            padding: dp(12)
            spacing: dp(8)
            TextInput:
                id: amount
                hint_text: "Montant FCFA"
                input_filter: "float"
                multiline: False
                size_hint_y: None
                height: dp(46)
            TextInput:
                id: category
                hint_text: "Catégorie"
                multiline: False
                size_hint_y: None
                height: dp(46)
            PrimaryButton:
                text: "Ajouter"
                on_release: root.add()
            BoxLayout:
                size_hint_y: None
                height: dp(46)
                spacing: dp(8)
                Button:
                    text: "Photo du reçu"
                    on_release: root.scan(True)
                Button:
                    text: "Reçu de la galerie"
                    on_release: root.scan(False)
            PrimaryButton:
                text: "Mode courses (panier avec budget)"
                size_hint_y: None
                height: dp(46)
                on_release: app.sm.current = "shopping"
            Button:
                text: "Réglages du scan (clé Gemini)"
                size_hint_y: None
                height: dp(36)
                font_size: "13sp"
                on_release: root.key_dialog()
            Label:
                id: total
                text: "Total : 0 F"
                font_size: "18sp"
                bold: True
                size_hint_y: None
                height: dp(34)
            ScrollView:
                Label:
                    id: listing
                    text: ""
                    halign: "left"
                    valign: "top"
                    text_size: self.width, None
                    size_hint_y: None
                    height: self.texture_size[1]
            DangerButton:
                text: "Remettre les dépenses à zéro"
                on_release: app.ask_reset("expenses", root.on_enter)

<BonusScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "13e mois"
        BoxLayout:
            orientation: "vertical"
            padding: dp(14)
            spacing: dp(10)
            Image:
                source: "@@/h_mois.png"
                size_hint_y: None
                height: dp(80)
                fit_mode: "contain"
            TextInput:
                id: bonus
                hint_text: "Montant réellement reçu"
                input_filter: "float"
                multiline: False
                size_hint_y: None
                height: dp(54)
            Label:
                text: root.result
                halign: "left"
                valign: "top"
                text_size: self.width, None
            PrimaryButton:
                text: "Enregistrer le 13e mois"
                on_release: root.save()
            Label:
                text: "Répartition indépendante du salaire mensuel."
                color: .45,.50,.56,1
                font_size: "12sp"
                size_hint_y: None
                height: dp(28)
            DangerButton:
                text: "Remettre le 13e mois à zéro"
                on_release: app.ask_reset("bonus", root.on_enter)

<CommitmentsScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Scolarité / prêts"
        ScrollView:
            do_scroll_x: False
            BoxLayout:
                orientation: "vertical"
                padding: dp(12)
                spacing: dp(8)
                size_hint_y: None
                height: self.minimum_height

                Label:
                    text: "Scolarité"
                    font_size: "20sp"
                    bold: True
                    halign: "left"
                    valign: "middle"
                    text_size: self.size
                    size_hint_y: None
                    height: dp(36)
                TextInput:
                    id: child
                    hint_text: "Nom / enfant"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                TextInput:
                    id: school_amount
                    hint_text: "Montant total à payer (FCFA)"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                TextInput:
                    id: school_monthly
                    hint_text: "Provision / échéance mensuelle (FCFA)"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                TextInput:
                    id: school_due
                    hint_text: "Échéance : JJ-MM-AAAA"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                PrimaryButton:
                    text: "Ajouter l'échéance scolaire"
                    on_release: root.add_school()
                Label:
                    id: school_list
                    text: "Aucune échéance scolaire."
                    halign: "left"
                    valign: "top"
                    text_size: self.width, None
                    size_hint_y: None
                    height: self.texture_size[1]

                Label:
                    text: "Prêts en cours"
                    font_size: "20sp"
                    bold: True
                    halign: "left"
                    valign: "middle"
                    text_size: self.size
                    size_hint_y: None
                    height: dp(36)
                TextInput:
                    id: lender
                    hint_text: "Organisme / prêteur"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                TextInput:
                    id: principal
                    hint_text: "Montant initial du prêt"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                TextInput:
                    id: rate
                    hint_text: "Taux (%)"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                TextInput:
                    id: monthly
                    hint_text: "Échéance mensuelle"
                    input_filter: "float"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                TextInput:
                    id: loan_due
                    hint_text: "Date de fin : JJ-MM-AAAA"
                    multiline: False
                    size_hint_y: None
                    height: dp(46)
                PrimaryButton:
                    text: "Ajouter le prêt"
                    on_release: root.add_loan()
                Label:
                    id: loan_list
                    text: "Aucun prêt enregistré."
                    halign: "left"
                    valign: "top"
                    text_size: self.width, None
                    size_hint_y: None
                    height: self.texture_size[1]
                DangerButton:
                    text: "Remettre scolarité et prêts à zéro"
                    on_release: app.ask_reset("commitments", root.on_enter)

<HistoryScreen>:
    BoxLayout:
        orientation: "vertical"
        TopBar:
            title: "Historique"
        ScrollView:
            Label:
                id: history
                text: ""
                padding: dp(12), dp(10)
                halign: "left"
                valign: "top"
                text_size: self.width, None
                size_hint_y: None
                height: self.texture_size[1]
        BoxLayout:
            size_hint_y: None
            height: dp(68)
            padding: dp(10)
            PrimaryButton:
                text: "Actualiser"
                on_release: root.refresh()
"""


def money(n):
    return f"{n:,.0f}".replace(",", " ") + " F"


def popup(title, text, size=(.82, .25)):
    Popup(title=title, content=Label(text=text, halign="center"), size_hint=size).open()


class TopBar(BoxLayout):
    title = StringProperty("")
    back = StringProperty("home")


class StatCard(BoxLayout):
    title = StringProperty("")
    value = StringProperty("")
    bg = ListProperty([1, 1, 1, 1])
    fg = ListProperty([0, 0, 0, 1])


class IconTile(ButtonBehavior, BoxLayout):
    source = StringProperty("")
    text = StringProperty("")


class RowButton(ButtonBehavior, BoxLayout):
    source = StringProperty("")
    text = StringProperty("")


class RowCard(BoxLayout):
    pass


def _left_label(text, **kw):
    lab = Label(text=text, halign="left", valign="middle", **kw)
    lab.bind(size=lambda inst, val: setattr(inst, "text_size", (inst.width, inst.height)))
    return lab


def _right_label(text, **kw):
    lab = Label(text=text, halign="right", valign="middle", **kw)
    lab.bind(size=lambda inst, val: setattr(inst, "text_size", (inst.width, inst.height)))
    return lab



CHART_COLORS = ["2F80ED", "F2994A", "9B51E0", "F2C94C", "56CCF2", "F06292",
                "E53935", "43A047", "8D6E63", "26A69A", "3949AB"]


def hex_rgba(h, a=1):
    return [int(h[i:i + 2], 16) / 255 for i in (0, 2, 4)] + [a]


class ChartCard(BoxLayout):
    pass


class HBar(Widget):
    fraction = NumericProperty(0)
    color = ListProperty([.2, .5, .9, 1])


class VBar(Widget):
    fraction = NumericProperty(0)
    color = ListProperty([.2, .5, .9, 1])


class Dot(Widget):
    color = ListProperty([.2, .5, .9, 1])


class PieChart(Widget):
    """Graphique en anneau : data = [(valeur, (r,g,b,a)), ...]"""
    data = ListProperty([])
    center_text = StringProperty("")

    def __init__(self, **kw):
        super().__init__(**kw)
        self._lbl = Label(text="", font_size="15sp", bold=True, halign="center",
                          valign="middle")
        self.add_widget(self._lbl)
        for prop in ("data", "pos", "size", "center_text"):
            self.bind(**{prop: self.redraw})

    def redraw(self, *_):
        self.canvas.before.clear()
        d = min(self.width, self.height)
        if d <= 0:
            return
        cx, cy = self.center
        total = sum(v for v, _c in self.data) or 1
        with self.canvas.before:
            angle = 0
            for v, col in self.data:
                if v <= 0:
                    continue
                sweep = 360.0 * v / total
                Color(*col)
                Ellipse(pos=(cx - d / 2, cy - d / 2), size=(d, d),
                        angle_start=angle, angle_end=angle + sweep)
                angle += sweep
            Color(1, 1, 1, 1)
            h = d * .58
            Ellipse(pos=(cx - h / 2, cy - h / 2), size=(h, h))
        self._lbl.text = self.center_text
        self._lbl.size = (h, h)
        self._lbl.text_size = (h, h)
        self._lbl.center = self.center



FR_MONTHS = ["Janv.", "Févr.", "Mars", "Avr.", "Mai", "Juin", "Juil.", "Août",
             "Sept.", "Oct.", "Nov.", "Déc."]
PRIORITIES = ["Urgente", "Normale", "Secondaire"]
PRIORITY_RANK = {"Urgente": 0, "Normale": 1, "Secondaire": 2}
PRIORITY_STYLE = {
    "Urgente": ([1, .91, .80, 1], [.78, .38, 0, 1]),
    "Normale": ([.86, .93, 1, 1], [.04, .32, .62, 1]),
    "Secondaire": ([.93, .88, 1, 1], [.40, .20, .70, 1]),
}
GOAL_ICONS = [("maison", "Maison"), ("voiture", "Voiture"), ("etudes", "Études"),
              ("voyage", "Voyage"), ("projet", "Projet"), ("urgence", "Urgence")]
GREEN = [.09, .58, .34, 1]
WHITE = (1, 1, 1, 1)
GREY = (.45, .50, .56, 1)
POS_COLOR = (.02, .45, .18, 1)
NEG_COLOR = (.70, .08, .08, 1)


def parse_date(text):
    text = (text or "").strip()
    if not text:
        return None
    for fmt in ("%d-%m-%Y", "%d/%m/%Y", "%d.%m.%Y", "%Y-%m-%d", "%m/%Y", "%m-%Y"):
        try:
            return datetime.strptime(text, fmt).date()
        except ValueError:
            pass
    return None


def fmt_date(d):
    return d.strftime("%d/%m/%Y")


def fmt_month(d):
    return f"{FR_MONTHS[d.month - 1]} {d.year}"


def add_months(d, n):
    idx = d.month - 1 + n
    return dt_date(d.year + idx // 12, idx % 12 + 1, 1)


def months_left(due):
    """None = pas d'echeance ; -1 = depassee ; sinon nombre de mois calendaires restants."""
    if not due:
        return None
    today = dt_date.today()
    if due < today:
        return -1
    return (due.year - today.year) * 12 + due.month - today.month


def months_text(due):
    m = months_left(due)
    if m is None:
        return "Sans échéance"
    if m < 0:
        return "Échéance dépassée"
    if m == 0:
        return "Ce mois-ci"
    return "1 mois" if m == 1 else f"{m} mois"


def pct_of(saved, target):
    return 0 if target <= 0 else max(0, min(100, saved / target * 100))


def projected_date(g):
    remaining = g["target"] - g["saved"]
    if remaining <= 0 or g["monthly"] <= 0:
        return None
    # le versement du mois en cours compte comme le premier
    return add_months(dt_date.today(), math.ceil(remaining / g["monthly"]) - 1)


def required_monthly(g):
    remaining = g["target"] - g["saved"]
    if remaining <= 0 or not g["due"]:
        return None
    m = months_left(g["due"])
    if m is None or m < 0:
        return remaining
    return remaining / (m + 1)


class Tag(Label):
    bg = ListProperty([.9, .9, .9, 1])
    fg = ListProperty([.1, .1, .1, 1])


class HeroCard(BoxLayout):
    bg = ListProperty([.09, .58, .34, 1])


class StatIcon(BoxLayout):
    title = StringProperty("")
    value = StringProperty("")
    source = StringProperty("")
    bg = ListProperty([1, 1, 1, 1])
    fg = ListProperty([0, 0, 0, 1])


class ActionTile(ButtonBehavior, BoxLayout):
    source = StringProperty("")
    text = StringProperty("")


class GoalRow(ButtonBehavior, BoxLayout):
    pass


class IconPick(ButtonBehavior, BoxLayout):
    source = StringProperty("")
    text = StringProperty("")
    selected = BooleanProperty(False)


class SegButton(Button):
    active = BooleanProperty(False)
    act_color = ListProperty([.03, .55, .30, 1])


def section_title(text):
    lab = _left_label(text, font_size="16sp", bold=True)
    lab.size_hint_y = None
    lab.height = dp(30)
    return lab


def wrap_label(text, size="13sp", halign="left", **kw):
    lab = Label(text=text, font_size=size, halign=halign, valign="top",
                size_hint_y=None, **kw)
    lab.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
    lab.bind(texture_size=lambda i, ts: setattr(i, "height", ts[1] + dp(6)))
    return lab


def kv_row(label, value, color=None, bold=True):
    row = BoxLayout(size_hint_y=None, height=dp(26), spacing=dp(8))
    row.add_widget(_left_label(label, font_size="13sp", color=GREY, size_hint_x=.5,
                               shorten=True))
    kw = {"color": color} if color else {}
    row.add_widget(_right_label(value, font_size="13sp", bold=bold, shorten=True,
                                size_hint_x=.5, **kw))
    return row


def bar_row(name, value_text, fraction, color):
    row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
    row.add_widget(_left_label(name, font_size="12sp", size_hint_x=None, width=dp(104),
                               shorten=True))
    row.add_widget(HBar(fraction=max(0, min(1, fraction)), color=color))
    row.add_widget(_right_label(value_text, font_size="12sp", bold=True, size_hint_x=None,
                                width=dp(44)))
    return row


def confirm(title, text, on_yes, yes_text="Oui", no_text="Non"):
    content = BoxLayout(orientation="vertical", padding=dp(12), spacing=dp(10))
    lab = Label(text=text, halign="center", valign="middle")
    lab.bind(width=lambda i, w: setattr(i, "text_size", (w, None)))
    content.add_widget(lab)
    btns = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(10))
    pop = Popup(title=title, content=content, size_hint=(.88, .4))
    b_no = Button(text=no_text)
    b_yes = Button(text=yes_text, background_color=(.85, .22, .22, 1), color=WHITE)
    b_no.bind(on_release=lambda *_: pop.dismiss())

    def _yes(*_):
        pop.dismiss()
        on_yes()
    b_yes.bind(on_release=_yes)
    btns.add_widget(b_no)
    btns.add_widget(b_yes)
    content.add_widget(btns)
    pop.open()


def make_goal_row(g, show_due=False, show_tag=False, origin="goals"):
    app = App.get_running_app()
    row = GoalRow()
    row.height = dp(106) if show_due else dp(92)
    row.add_widget(Image(source=asset("g_" + g["icon"]), size_hint_x=None,
                         width=dp(72), fit_mode="contain"))
    col = BoxLayout(orientation="vertical", spacing=dp(1))
    top = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(6))
    top.add_widget(_left_label(g["name"], font_size="15sp", bold=True, shorten=True))
    if show_tag:
        bg, fg = PRIORITY_STYLE.get(g["priority"], PRIORITY_STYLE["Normale"])
        top.add_widget(Tag(text=g["priority"], bg=bg, fg=fg, pos_hint={"center_y": .5}))
    col.add_widget(top)
    note = _left_label(g["note"] or " ", font_size="11sp", color=GREY, shorten=True)
    note.size_hint_y = None
    note.height = dp(16)
    col.add_widget(note)
    pct = pct_of(g["saved"], g["target"])
    amounts = BoxLayout(size_hint_y=None, height=dp(20))
    amounts.add_widget(_left_label(f"[b]{money(g['saved'])}[/b] / {money(g['target'])}",
                                   markup=True, font_size="12sp"))
    amounts.add_widget(_right_label(f"{pct:.0f} %", size_hint_x=None, width=dp(44),
                                    font_size="12sp", bold=True))
    col.add_widget(amounts)
    col.add_widget(HBar(fraction=pct / 100, color=GREEN, size_hint_y=None, height=dp(14)))
    if show_due:
        d = g["due"]
        txt = months_text(d) + (f"   ({fmt_month(d)})" if d else "")
        due_lab = _left_label(txt, font_size="11sp", color=GREY)
        due_lab.size_hint_y = None
        due_lab.height = dp(18)
        col.add_widget(due_lab)
    row.add_widget(col)
    row.add_widget(Label(text="›", font_size="24sp", size_hint_x=None, width=dp(16),
                         color=(.60, .65, .70, 1)))
    row.bind(on_release=lambda *_: app.open_goal(g["id"], origin))
    return row


NAV_ITEMS = [
    ("Accueil", "g_maison", "home"),
    ("Salaire net", "wallet", "salary"),
    ("Budget mensuel", "h_budget", "budget"),
    ("Épargne", "h_epargne", "savings"),
    ("Objectifs", "h_obj", "goals"),
    ("Dépenses", "h_dep", "expenses"),
    ("Courses", "cat_alimentation", "shopping"),
    ("13e mois", "h_mois", "bonus"),
    ("Scolarité / prêts", "cat_famille", "commitments"),
    ("Rapports", "h_rapport", "reports"),
    ("Historique", "h_dep", "history"),
]

RESETS = {
    "expenses": ("Dépenses", "Supprime toutes les dépenses saisies."),
    "salary": ("Salaire net", "Efface les salaires enregistrés : le salaire net revient à 0 F."),
    "bonus": ("13e mois", "Efface les montants de 13e mois enregistrés."),
    "savings": ("Épargne", "Supprime tous les versements et retraits. Les objectifs sont "
                           "conservés, avec une progression à 0."),
    "goals": ("Objectifs", "Supprime tous les objectifs. L'argent déjà épargné passe en "
                           "épargne libre."),
    "commitments": ("Scolarité et prêts", "Supprime les échéances scolaires et les prêts "
                                          "enregistrés."),
    "budget": ("Budget et alimentation", "Rétablit les pourcentages du budget et les montants "
                                         "d'alimentation par défaut."),
    "budget_pct": ("Pourcentages du budget", "Rétablit les pourcentages par défaut "
                                             "(25 % logement, 25 % alimentation...)."),
    "food": ("Alimentation", "Rétablit les montants par défaut du détail alimentation."),
    "all": ("Toute l'application", "Remet TOUT à zéro : salaire, dépenses, 13e mois, épargne, "
                                   "objectifs, scolarité, prêts et budget."),
}
RESET_ORDER = ["expenses", "salary", "bonus", "savings", "goals", "commitments", "budget"]


def plural(n, word):
    return f"{n} {word}{'s' if n > 1 else ''}"


class MenuButton(ButtonBehavior, Widget):
    pass


class MenuItem(ButtonBehavior, BoxLayout):
    source = StringProperty("")
    text = StringProperty("")
    fg = ListProperty([.10, .18, .27, 1])
    active = BooleanProperty(False)


class SideMenu(FloatLayout):
    """Tiroir qui glisse depuis la gauche : s'ouvre avec les 3 traits de l'accueil."""

    def __init__(self, app, **kw):
        super().__init__(**kw)
        self.app = app
        self.closing = False
        self.width_px = min(dp(310), Window.width * .84)
        shade = Button(background_normal="", background_down="",
                       background_color=(0, 0, 0, .45), size_hint=(1, 1))
        shade.bind(on_release=lambda *_: self.dismiss())
        self.add_widget(shade)

        drawer = Factory.Drawer(orientation="vertical", size_hint=(None, 1),
                                width=self.width_px)
        self.drawer = drawer
        head = Factory.DrawerHead(size_hint_y=None, height=dp(132), padding=dp(16),
                                  spacing=dp(14))
        head.add_widget(Image(source=asset("app_icon"), size_hint_x=None, width=dp(72),
                              fit_mode="contain"))
        col = BoxLayout(orientation="vertical")
        col.add_widget(_left_label("MON SALAIRE", font_size="19sp", bold=True, color=WHITE))
        col.add_widget(_left_label("Salaire net", font_size="12sp", color=(.80, .88, .96, 1)))
        col.add_widget(_left_label(money(app.current_salary()), font_size="18sp", bold=True,
                                   color=WHITE))
        head.add_widget(col)
        drawer.add_widget(head)

        scroll = ScrollView(do_scroll_x=False)
        items = BoxLayout(orientation="vertical", size_hint_y=None)
        items.bind(minimum_height=items.setter("height"))
        current = app.sm.current
        for text, icon, screen in NAV_ITEMS:
            it = MenuItem(source=asset(icon), text=text, active=(screen == current))
            it.bind(on_release=lambda w, sc=screen: self.go(sc))
            items.add_widget(it)
        scroll.add_widget(items)
        drawer.add_widget(scroll)
        sep = BoxLayout(size_hint_y=None, height=dp(1))
        with sep.canvas:
            Color(.86, .89, .93, 1)
            self._sep = Rectangle(pos=sep.pos, size=sep.size)
        sep.bind(pos=lambda w, v: setattr(self._sep, "pos", v),
                 size=lambda w, v: setattr(self._sep, "size", v))
        drawer.add_widget(sep)
        lab = wrap_label("  DONNÉES", size="11sp", bold=True, color=GREY)
        lab.size_hint_y = None
        lab.height = dp(26)
        drawer.add_widget(lab)
        reset = MenuItem(source=asset("reset"), text="Remise à zéro",
                         fg=[.70, .08, .08, 1], active=(current == "reset"))
        reset.bind(on_release=lambda w: self.go("reset"))
        drawer.add_widget(reset)
        foot = wrap_label("Ma famille • Mon budget • Mon avenir", size="11sp",
                          halign="center", color=GREY)
        foot.size_hint_y = None
        foot.height = dp(32)
        drawer.add_widget(foot)
        drawer.x = -self.width_px
        self.add_widget(drawer)

    def open(self):
        Window.add_widget(self)
        Animation(x=0, d=.2, t="out_quad").start(self.drawer)

    def go(self, screen):
        self.dismiss()
        self.app.sm.current = screen

    def dismiss(self, *_):
        if self.closing:
            return
        self.closing = True
        anim = Animation(x=-self.width_px, d=.15, t="in_quad")
        anim.bind(on_complete=lambda *a: self._remove())
        anim.start(self.drawer)

    def _remove(self):
        if self.parent:
            Window.remove_widget(self)
        if self.app._menu is self:
            self.app._menu = None


class DBMixin:
    def init_db(self):
        old_db = getattr(self, "db", None)
        if old_db is not None:
            try:
                old_db.close()
            except Exception:
                pass
        db_path = Path(str(self.user_data_dir)) / "mon_salaire.db"
        db_path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(str(db_path))
        self.db.execute("""CREATE TABLE IF NOT EXISTS settings(
            key TEXT PRIMARY KEY, value TEXT NOT NULL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS expenses(
            id INTEGER PRIMARY KEY, date TEXT, amount REAL, category TEXT)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS cart(
            id INTEGER PRIMARY KEY, name TEXT, price REAL, qty INTEGER DEFAULT 1)""")
        try:
            self.db.execute("ALTER TABLE expenses ADD COLUMN note TEXT")
        except sqlite3.OperationalError:
            pass
        self.db.execute("""CREATE TABLE IF NOT EXISTS bonus(
            id INTEGER PRIMARY KEY, date TEXT, amount REAL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS salaries(
            id INTEGER PRIMARY KEY, date TEXT, amount REAL)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS schooling(
            id INTEGER PRIMARY KEY, date TEXT, child TEXT, amount REAL,
            monthly REAL DEFAULT 0, due_date TEXT, status TEXT)""")
        self.db.execute("""CREATE TABLE IF NOT EXISTS loans(
            id INTEGER PRIMARY KEY, date TEXT, lender TEXT, principal REAL,
            rate REAL, monthly_payment REAL, due_date TEXT, remaining REAL)""")
        self._ensure_table("goals", """CREATE TABLE goals(
            id INTEGER PRIMARY KEY, name TEXT NOT NULL, note TEXT, target REAL NOT NULL,
            due_date TEXT, priority TEXT DEFAULT 'Normale', monthly REAL DEFAULT 0,
            icon TEXT DEFAULT 'projet', created TEXT)""",
                           ("id", "name", "note", "target", "due_date", "priority",
                            "monthly", "icon", "created"))
        self._ensure_table("savings", """CREATE TABLE savings(
            id INTEGER PRIMARY KEY, date TEXT, amount REAL, goal_id INTEGER, note TEXT)""",
                           ("id", "date", "amount", "goal_id", "note"))
        try:
            self.db.execute("ALTER TABLE schooling ADD COLUMN monthly REAL DEFAULT 0")
        except sqlite3.OperationalError:
            pass
        for i, (_, name, pct) in enumerate(DEFAULT_BUDGET):
            self.db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",
                            (f"pct_{i}", str(pct)))
        for i, (_, name, amount) in enumerate(FOOD_DEFAULT):
            self.db.execute("INSERT OR IGNORE INTO settings(key,value) VALUES(?,?)",
                            (f"food_{i}", str(amount)))
        self.db.commit()

    def _ensure_table(self, name, create_sql, required):
        """Cree la table ; si une ancienne table de meme nom a d'autres colonnes
        (version precedente), elle est conservee sous un autre nom (rien n'est perdu)."""
        cols = {r[1] for r in self.db.execute(f"PRAGMA table_info({name})").fetchall()}
        if cols and not set(required) <= cols:
            stamp = datetime.now().strftime("%Y%m%d%H%M%S")
            self.db.execute(f"ALTER TABLE {name} RENAME TO {name}_ancien_{stamp}")
            cols = set()
        if not cols:
            self.db.execute(create_sql)

    def setting(self, key, default=0):
        row = self.db.execute("SELECT value FROM settings WHERE key=?", (key,)).fetchone()
        return float(row[0]) if row else default

    def set_setting(self, key, value):
        self.db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",
                        (key, str(value)))


class StartupScreen(Screen):
    def on_enter(self):
        # Attendre que tous les ecrans soient ajoutes au ScreenManager
        from kivy.clock import Clock
        Clock.schedule_once(lambda dt: App.get_running_app().startup(), .3)


class HomeScreen(Screen):
    salary_text = StringProperty("0 F")
    expenses_text = StringProperty("0 F")
    savings_text = StringProperty("0 F")
    remaining_text = StringProperty("0 F")

    def on_enter(self):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        salary = app.current_salary()
        expenses = app.total_expenses()
        commitments = app.monthly_commitments()
        savings = salary * app.budget_pct(9) / 100
        self.salary_text = money(salary)
        self.expenses_text = money(expenses)
        self.savings_text = money(savings)
        self.remaining_text = money(max(0, salary - expenses - commitments))

    def go(self, screen):
        App.get_running_app().sm.current = screen


class SalaryScreen(Screen):
    preview = StringProperty("")

    def on_enter(self):
        value = App.get_running_app().current_salary()
        self.ids.salary.text = str(int(value)) if value else ""
        self.update_preview()

    def update_preview(self):
        try:
            value = float(self.ids.salary.text or 0)
            self.preview = f"Salaire net disponible : {money(value)}"
        except Exception:
            self.preview = "Montant invalide."

    def save(self):
        try:
            value = float(self.ids.salary.text or 0)
            if value < 0:
                raise ValueError
            app = App.get_running_app()
            app.db.execute("INSERT INTO salaries(date,amount) VALUES(?,?)",
                           (datetime.now().strftime("%Y-%m-%d"), value))
            app.db.commit()
            self.update_preview()
            popup("Salaire enregistré", f"{money(value)} enregistré.")
            app.sm.current = "home"
        except Exception:
            self.preview = "Veuillez saisir un montant valide."


class BudgetScreen(Screen):
    total_text = StringProperty("")
    inputs = []

    def on_enter(self):
        self.build_rows()

    def build_rows(self):
        self.ids.rows.clear_widgets()
        self.inputs = []
        app = App.get_running_app()
        salary = app.current_salary()
        for i, (key, name, pct) in enumerate(DEFAULT_BUDGET):
            row = RowCard()
            row.add_widget(Image(source=asset("cat_" + key), size_hint_x=None,
                                 width=dp(50), fit_mode="contain"))
            row.add_widget(_left_label(name, font_size="13sp", bold=True))
            inp = TextInput(text=f"{app.budget_pct(i):g}", input_filter="float",
                            multiline=False, size_hint=(None, None),
                            size=(dp(52), dp(36)), pos_hint={"center_y": .5},
                            halign="center", padding=[dp(4), dp(8)])
            row.add_widget(inp)
            row.add_widget(Label(text="%", size_hint_x=None, width=dp(14), font_size="13sp"))
            amount = _right_label(money(salary * app.budget_pct(i) / 100),
                                  size_hint_x=None, width=dp(84), font_size="13sp", bold=True)
            inp.bind(text=lambda inst, val, idx=i, amt=amount: self.update_amount(idx, amt, val))
            row.add_widget(amount)
            if key == "alimentation":
                btn = Button(text="›", size_hint_x=None, width=dp(30), font_size="26sp",
                             background_color=(0, 0, 0, 0), color=(.04, .30, .55, 1))
                btn.bind(on_release=lambda *_: setattr(app.sm, "current", "food"))
            else:
                btn = Label(text="›", size_hint_x=None, width=dp(30), font_size="26sp",
                            color=(.60, .65, .70, 1))
            row.add_widget(btn)
            self.ids.rows.add_widget(row)
            self.inputs.append(inp)
        self.update_total()

    def update_amount(self, idx, label, value):
        try:
            pct = float(value or 0)
            label.text = money(App.get_running_app().current_salary() * pct / 100)
        except Exception:
            label.text = "0 F"
        self.update_total()

    def update_total(self):
        total = 0
        for x in self.inputs:
            try:
                total += float(x.text or 0)
            except Exception:
                pass
        self.total_text = f"TOTAL : {total:.0f} %"

    def save(self):
        app = App.get_running_app()
        total = 0
        vals = []
        for i, inp in enumerate(self.inputs):
            try:
                v = float(inp.text or 0)
            except Exception:
                v = 0
            vals.append(v)
            total += v
        if abs(total - 100) > 0.01:
            popup("Répartition invalide",
                  f"Les pourcentages doivent totaliser 100 %.\nActuellement : {total:.2f} %.",
                  size=(.85, .3))
            return
        for i, v in enumerate(vals):
            app.set_setting(f"pct_{i}", v)
        app.db.commit()
        popup("Budget enregistré", "Nouvelle répartition enregistrée.")
        self.build_rows()


class FoodScreen(Screen):
    total_text = StringProperty("")
    inputs = []

    def on_enter(self):
        self.build()

    def build(self):
        app = App.get_running_app()
        self.ids.food_rows.clear_widgets()
        self.inputs = []
        for i, (key, name, default) in enumerate(FOOD_DEFAULT):
            row = RowCard()
            row.height = dp(66)
            row.add_widget(Image(source=asset(key), size_hint_x=None, width=dp(60),
                                 fit_mode="contain"))
            row.add_widget(_left_label(name, font_size="14sp", bold=True))
            inp = TextInput(text=f"{app.food_amount(i):.0f}", input_filter="float",
                            multiline=False, size_hint=(None, None),
                            size=(dp(96), dp(38)), pos_hint={"center_y": .5},
                            halign="right", padding=[dp(6), dp(9)])
            inp.bind(text=lambda *_: self.update_total())
            row.add_widget(inp)
            row.add_widget(Label(text="F", size_hint_x=None, width=dp(16), font_size="13sp"))
            self.ids.food_rows.add_widget(row)
            self.inputs.append(inp)
        self.update_total()

    def update_total(self):
        try:
            total = sum(float(x.text or 0) for x in self.inputs)
        except Exception:
            total = 0
        self.total_text = money(total)

    def save(self):
        app = App.get_running_app()
        total = 0
        for i, inp in enumerate(self.inputs):
            try:
                v = max(0, float(inp.text or 0))
            except Exception:
                v = 0
            app.set_setting(f"food_{i}", v)
            total += v
        app.db.commit()
        self.total_text = money(total)
        popup("Alimentation enregistrée", f"Total : {money(total)}")


class ShoppingScreen(Screen):
    """Panier de courses : chaque article est compare au budget de la categorie."""

    def on_enter(self):
        names = [n for _k, n, _p in DEFAULT_BUDGET]
        self.ids.cat.values = names
        if self.ids.cat.text not in names:
            self.ids.cat.text = "Alimentation"
        self.refresh()

    # ----- chiffres
    def _index(self):
        names = [n for _k, n, _p in DEFAULT_BUDGET]
        return names.index(self.ids.cat.text) if self.ids.cat.text in names else 1

    def budget(self):
        app = App.get_running_app()
        return app.current_salary() * app.budget_pct(self._index()) / 100

    def spent(self):
        row = App.get_running_app().db.execute(
            "SELECT COALESCE(SUM(amount),0) FROM expenses WHERE category=?",
            (self.ids.cat.text,)).fetchone()
        return float(row[0])

    def cart_total(self):
        row = App.get_running_app().db.execute(
            "SELECT COALESCE(SUM(price*qty),0) FROM cart").fetchone()
        return float(row[0])

    def remaining(self):
        return self.budget() - self.spent() - self.cart_total()

    # ----- affichage
    def refresh(self):
        if "cat" not in self.ids:
            return
        app = App.get_running_app()
        if app.db is None:
            return
        budget, spent, cart = self.budget(), self.spent(), self.cart_total()
        rest = budget - spent - cart
        self.ids.line1.text = (f"Budget {money(budget)}  •  Déjà dépensé {money(spent)}"
                               f"  •  Panier {money(cart)}")
        if rest < 0:
            self.ids.remain.text = f"Dépassement : {money(-rest)}"
            color = (.80, .12, .12, 1)
        else:
            self.ids.remain.text = f"Reste : {money(rest)}"
            color = (.05, .55, .28, 1) if budget and rest / budget >= .2 else (.90, .50, .05, 1)
        self.ids.remain.color = color
        self.ids.bar.color = list(color)
        self.ids.bar.fraction = min(1, (spent + cart) / budget) if budget > 0 else 1
        box = self.ids.cart
        box.clear_widgets()
        rows = app.db.execute("SELECT id,name,price,qty FROM cart ORDER BY id DESC").fetchall()
        if not rows:
            box.add_widget(wrap_label("Panier vide. Ajoutez les articles au fur et à mesure.",
                                      size="13sp", color=GREY))
        for cid, name, price, qty in rows:
            row = RowCard()
            row.height = dp(52)
            txt = name if qty == 1 else f"{name}  x{qty}"
            row.add_widget(_left_label(txt, font_size="14sp", bold=True, shorten=True))
            row.add_widget(_right_label(money(price * qty), font_size="13sp", bold=True,
                                        size_hint_x=None, width=dp(84)))
            btn = Button(text="Retirer", size_hint_x=None, width=dp(64), font_size="12sp")
            btn.bind(on_release=lambda w, i=cid: self.remove(i))
            row.add_widget(btn)
            box.add_widget(row)

    # ----- actions
    def add(self, force=False):
        app = App.get_running_app()
        name = self.ids.name.text.strip()
        try:
            price = float(self.ids.price.text or 0)
            qty = int(self.ids.qty.text or 1)
        except ValueError:
            price, qty = 0, 0
        if not name or price <= 0 or qty <= 0:
            popup("Article incomplet", "Indiquez le nom, le prix et la quantité.", (.85, .25))
            return
        total = price * qty
        rest_after = self.remaining() - total
        if rest_after < 0 and not force:
            confirm("Budget dépassé",
                    f"Cet article dépasse le budget « {self.ids.cat.text} » de "
                    f"{money(-rest_after)}.\n(Reste avant l'article : {money(self.remaining())})\n\n"
                    "Ajouter quand même ?",
                    lambda: self.add(True), yes_text="Ajouter", no_text="Annuler")
            return
        app.db.execute("INSERT INTO cart(name,price,qty) VALUES(?,?,?)", (name, price, qty))
        app.db.commit()
        self.ids.name.text = ""
        self.ids.price.text = ""
        self.ids.qty.text = "1"
        self.refresh()
        if 0 <= rest_after < .1 * self.budget():
            popup("Attention", f"Il ne reste que {money(rest_after)} sur ce budget.",
                  (.85, .25))

    def remove(self, cart_id):
        App.get_running_app().db.execute("DELETE FROM cart WHERE id=?", (cart_id,))
        App.get_running_app().db.commit()
        self.refresh()

    def clear_cart(self):
        confirm("Vider le panier", "Retirer tous les articles du panier ?",
                self._do_clear, yes_text="Vider", no_text="Non")

    def _do_clear(self):
        App.get_running_app().db.execute("DELETE FROM cart")
        App.get_running_app().db.commit()
        self.refresh()

    def validate(self):
        app = App.get_running_app()
        rows = app.db.execute("SELECT name,price,qty FROM cart ORDER BY id").fetchall()
        if not rows:
            popup("Panier vide", "Aucun article à enregistrer.", (.8, .22))
            return
        today = datetime.now().strftime("%Y-%m-%d")
        total = 0
        for name, price, qty in rows:
            note = name if qty == 1 else f"{name} x{qty}"
            app.db.execute("INSERT INTO expenses(date,amount,category,note) VALUES(?,?,?,?)",
                           (today, price * qty, self.ids.cat.text, note))
            total += price * qty
        app.db.execute("DELETE FROM cart")
        app.db.commit()
        self.refresh()
        popup("Achats enregistrés",
              f"{len(rows)} article(s) • {money(total)}\nAjoutés aux dépenses ({self.ids.cat.text}).",
              (.85, .3))


class ExpensesScreen(Screen):
    receipt_date = None

    def on_enter(self):
        self.refresh()

    # ---------------------------------------------------- scan d'un reçu
    def _key_file(self):
        return Path(str(App.get_running_app().user_data_dir)) / "gemini_key.txt"

    def get_key(self):
        try:
            return self._key_file().read_text(encoding="utf-8").strip()
        except Exception:
            return ""

    def key_dialog(self, then=None):
        box = BoxLayout(orientation="vertical", padding=dp(10), spacing=dp(8))
        box.add_widget(wrap_label(
            "Clé gratuite : aistudio.google.com > « Get API key ». "
            "Elle reste uniquement sur ce téléphone.", size="13sp"))
        field = TextInput(text=self.get_key(), hint_text="Collez la clé ici",
                          multiline=False, size_hint_y=None, height=dp(46))
        box.add_widget(field)
        row = BoxLayout(size_hint_y=None, height=dp(46), spacing=dp(8))
        pop = Popup(title="Clé Gemini", content=box, size_hint=(.92, .5))

        def save(*_):
            try:
                self._key_file().write_text(field.text.strip(), encoding="utf-8")
            except Exception:
                popup("Erreur", "Clé non enregistrée.")
            pop.dismiss()
            if then and field.text.strip():
                then()
        ok = Button(text="Enregistrer")
        ok.bind(on_release=save)
        no = Button(text="Fermer")
        no.bind(on_release=lambda *_: pop.dismiss())
        row.add_widget(no)
        row.add_widget(ok)
        box.add_widget(row)
        pop.open()

    def scan(self, camera):
        if not self.get_key():
            self.key_dialog(then=lambda: self.scan(camera))
            return
        import imagepick
        imagepick.pick(self._got_image, camera=camera,
                       workdir=str(App.get_running_app().user_data_dir))

    def _got_image(self, path, err):
        if err:
            Clock.schedule_once(lambda dt: popup("Scan impossible", err, (.88, .4)))
            return
        if not path:
            return
        self._wait = Popup(title="Lecture du reçu…", content=Label(text="Veuillez patienter"),
                           size_hint=(.7, .2), auto_dismiss=False)
        self._wait.open()
        key = self.get_key()
        import threading
        threading.Thread(target=self._read, args=(path, key), daemon=True).start()

    def _read(self, path, key):
        import receipt
        try:
            res, err = receipt.extract(path, key), ""
        except receipt.ReceiptError as exc:
            res, err = None, str(exc)
        except Exception as exc:  # noqa
            res, err = None, "Erreur : " + str(exc)
        Clock.schedule_once(lambda dt: self._scan_done(res, err))

    def _scan_done(self, res, err):
        try:
            self._wait.dismiss()
        except Exception:
            pass
        if err:
            popup("Scan impossible", err, (.88, .4))
            return
        self.ids.amount.text = str(int(res["amount"]) if res["amount"] == int(res["amount"])
                                   else res["amount"])
        self.ids.category.text = res["category"]
        self.receipt_date = res["date"] or None
        who = f"\n{res['merchant']}" if res["merchant"] else ""
        popup("Reçu lu", f"{money(res['amount'])}{who}\n{res['date'] or 'date du jour'}\n\n"
              "Vérifiez, puis appuyez sur « Ajouter ».", (.88, .45))

    def add(self):
        try:
            amount = float(self.ids.amount.text or 0)
            category = self.ids.category.text.strip() or "Autre"
            if amount <= 0:
                raise ValueError
            app = App.get_running_app()
            app.db.execute("INSERT INTO expenses(date,amount,category) VALUES(?,?,?)",
                           (self.receipt_date or datetime.now().strftime("%Y-%m-%d"),
                            amount, category))
            app.db.commit()
            self.receipt_date = None
            self.ids.amount.text = ""
            self.ids.category.text = ""
            self.refresh()
        except Exception:
            pass

    def refresh(self):
        app = App.get_running_app()
        total = app.total_expenses()
        self.ids.total.text = f"Total : {money(total)}"
        rows = app.db.execute(
            "SELECT date,amount,category,note FROM expenses ORDER BY id DESC LIMIT 50").fetchall()
        self.ids.listing.text = "\n".join(
            f"{d}  •  {money(a)}  •  {c}" + (f"  •  {n}" if n else "")
            for d, a, c, n in rows) or "Aucune dépense enregistrée."


class BonusScreen(Screen):
    result = StringProperty("")

    def on_enter(self):
        row = App.get_running_app().db.execute(
            "SELECT amount FROM bonus ORDER BY id DESC LIMIT 1").fetchone()
        self.ids.bonus.text = str(int(row[0])) if row else ""
        self.update()

    def update(self):
        try:
            v = float(self.ids.bonus.text or 0)
            self.result = (f"13e mois disponible : {money(v)}\n\nExemple de répartition personnelle :\n"
                           "Épargne 30 % • Famille 20 % • Projets 20 % • Dettes 15 % • "
                           "Fêtes 10 % • Imprévus 5 %")
        except Exception:
            self.result = "Montant invalide."

    def save(self):
        try:
            v = float(self.ids.bonus.text or 0)
            if v < 0:
                raise ValueError
            app = App.get_running_app()
            app.db.execute("INSERT INTO bonus(date,amount) VALUES(?,?)",
                           (datetime.now().strftime("%Y-%m-%d"), v))
            app.db.commit()
            self.update()
            popup("13e mois enregistré", money(v))
        except Exception:
            self.result = "Veuillez saisir un montant valide."


class CommitmentsScreen(Screen):
    def on_enter(self):
        self.refresh()

    def add_school(self):
        try:
            child = self.ids.child.text.strip() or "Enfant"
            amount = float(self.ids.school_amount.text or 0)
            monthly = float(self.ids.school_monthly.text or 0)
            due = self.ids.school_due.text.strip() or "Non précisée"
            if amount <= 0 or monthly < 0 or monthly > amount:
                raise ValueError
            app = App.get_running_app()
            app.db.execute(
                "INSERT INTO schooling(date,child,amount,monthly,due_date,status) VALUES(?,?,?,?,?,?)",
                (datetime.now().strftime("%Y-%m-%d"), child, amount, monthly, due, "À payer"))
            app.db.commit()
            self.ids.child.text = ""
            self.ids.school_amount.text = ""
            self.ids.school_monthly.text = ""
            self.ids.school_due.text = ""
            self.refresh()
        except Exception:
            popup("Erreur", "Vérifiez le montant de scolarité.")

    def add_loan(self):
        try:
            lender = self.ids.lender.text.strip() or "Prêt"
            principal = float(self.ids.principal.text or 0)
            rate = float(self.ids.rate.text or 0)
            monthly = float(self.ids.monthly.text or 0)
            due = self.ids.loan_due.text.strip() or "Non précisée"
            if principal <= 0 or rate < 0 or monthly < 0:
                raise ValueError
            app = App.get_running_app()
            app.db.execute(
                """INSERT INTO loans(date,lender,principal,rate,monthly_payment,due_date,remaining)
                   VALUES(?,?,?,?,?,?,?)""",
                (datetime.now().strftime("%Y-%m-%d"), lender, principal, rate, monthly, due, principal))
            app.db.commit()
            for k in ("lender", "principal", "rate", "monthly", "loan_due"):
                self.ids[k].text = ""
            self.refresh()
        except Exception:
            popup("Erreur", "Vérifiez les données du prêt.")

    def refresh(self):
        app = App.get_running_app()
        schools = app.db.execute(
            "SELECT child,amount,monthly,due_date,status FROM schooling ORDER BY id DESC").fetchall()
        loans = app.db.execute(
            "SELECT lender,principal,rate,monthly_payment,due_date,remaining FROM loans ORDER BY id DESC"
        ).fetchall()

        school_total = sum(r[1] for r in schools)
        school_monthly = sum(r[2] for r in schools)
        loan_monthly = sum(r[3] for r in loans)
        self.ids.school_list.text = (
            "\n".join(
                f"{child} • total {money(amount)} • provision {money(monthly)}/mois • "
                f"échéance {due} • {status}"
                for child, amount, monthly, due, status in schools
            ) if schools else "Aucune échéance scolaire."
        ) + f"\n\nTotal scolarité : {money(school_total)}"
        self.ids.loan_list.text = (
            "\n".join(
                f"{lender} • restant {money(rem)}\n"
                f"   Initial {money(principal)} • taux {rate:g}% • "
                f"mensualité {money(monthly)} • fin {due}"
                for lender, principal, rate, monthly, due, rem in loans
            ) if loans else "Aucun prêt enregistré."
        ) + f"\n\nTotal mensualités prêts : {money(loan_monthly)}\n"
        self.ids.loan_list.text += f"Provision scolarité mensuelle : {money(school_monthly)}\n"
        self.ids.loan_list.text += f"Engagements mensuels : {money(school_monthly + loan_monthly)}"


class ReportsScreen(Screen):
    def on_enter(self):
        self.build()

    @staticmethod
    def _title(text):
        lab = _left_label(text, font_size="16sp", bold=True)
        lab.size_hint_y = None
        lab.height = dp(28)
        return lab

    @staticmethod
    def _note(text):
        lab = _left_label(text, font_size="13sp", color=(.45, .50, .56, 1))
        lab.size_hint_y = None
        lab.height = dp(40)
        return lab

    def _bar_row(self, name, value_text, fraction, color):
        row = BoxLayout(size_hint_y=None, height=dp(28), spacing=dp(6))
        n = _left_label(name, font_size="12sp", size_hint_x=.34, shorten=True)
        row.add_widget(n)
        row.add_widget(HBar(fraction=max(0, min(1, fraction)), color=color))
        row.add_widget(_right_label(value_text, font_size="12sp", bold=True, size_hint_x=.28))
        return row

    def build(self):
        app = App.get_running_app()
        box = self.ids.content
        box.clear_widgets()
        salary = app.current_salary()

        # 1) Repartition du budget (anneau + legende)
        card = ChartCard()
        card.add_widget(self._title("Répartition du budget"))
        data = [(app.budget_pct(i), hex_rgba(CHART_COLORS[i]))
                for i in range(len(DEFAULT_BUDGET))]
        pie = PieChart(size_hint_y=None, height=dp(210), data=data,
                       center_text=money(salary) if salary else "100 %")
        card.add_widget(pie)
        legend = GridLayout(cols=2, size_hint_y=None, spacing=dp(2))
        legend.bind(minimum_height=legend.setter("height"))
        for i, (_k, name, _p) in enumerate(DEFAULT_BUDGET):
            item = BoxLayout(size_hint_y=None, height=dp(24), spacing=dp(6))
            item.add_widget(Dot(color=hex_rgba(CHART_COLORS[i])))
            item.add_widget(_left_label(f"{name}  {app.budget_pct(i):g} %", font_size="12sp",
                                        shorten=True))
            legend.add_widget(item)
        card.add_widget(legend)
        box.add_widget(card)

        # 2) Depenses par categorie
        card = ChartCard()
        card.add_widget(self._title("Dépenses par catégorie"))
        total = app.total_expenses()
        rows = app.db.execute(
            "SELECT category, SUM(amount) FROM expenses GROUP BY category "
            "ORDER BY 2 DESC LIMIT 8").fetchall()
        if not rows:
            card.add_widget(self._note("Aucune dépense enregistrée."))
        else:
            if salary > 0:
                pct = total / salary * 100
                card.add_widget(self._note(
                    f"Total dépensé : {money(total)} sur {money(salary)} de salaire ({pct:.0f} %)."))
                over = total > salary
                card.add_widget(self._bar_row("Salaire utilisé", f"{pct:.0f} %", total / salary,
                                              [.85, .2, .2, 1] if over else [.09, .58, .34, 1]))
            else:
                card.add_widget(self._note(f"Total dépensé : {money(total)}."))
            top = rows[0][1] or 1
            for i, (cat, amount) in enumerate(rows):
                card.add_widget(self._bar_row(cat, money(amount), amount / top,
                                              hex_rgba(CHART_COLORS[i % len(CHART_COLORS)])))
        box.add_widget(card)

        # 3) Evolution du salaire net
        card = ChartCard()
        card.add_widget(self._title("Évolution du salaire net"))
        sal = app.db.execute(
            "SELECT date, amount FROM salaries ORDER BY id DESC LIMIT 6").fetchall()[::-1]
        if len(sal) < 2:
            card.add_widget(self._note(
                "Enregistre au moins deux salaires pour voir l'évolution."))
        else:
            top = max(a for _d, a in sal) or 1
            cols = BoxLayout(size_hint_y=None, height=dp(180), spacing=dp(2))
            for d, a in sal:
                col = BoxLayout(orientation="vertical")
                col.add_widget(Label(text=f"{a / 1000:.0f}k", font_size="11sp", bold=True,
                                     size_hint_y=None, height=dp(18)))
                col.add_widget(VBar(fraction=a / top, color=[.09, .58, .34, 1]))
                label_date = f"{d[8:10]}/{d[5:7]}" if len(d) >= 10 else d
                col.add_widget(Label(text=label_date, font_size="11sp",
                                     size_hint_y=None, height=dp(18),
                                     color=(.45, .50, .56, 1)))
                cols.add_widget(col)
            card.add_widget(cols)
        box.add_widget(card)

        btn = Button(text="Voir l'historique détaillé", size_hint_y=None, height=dp(48))
        btn.bind(on_release=lambda *_: setattr(app.sm, "current", "history"))
        box.add_widget(btn)


class HistoryScreen(Screen):
    def on_enter(self):
        self.refresh()

    def refresh(self):
        app = App.get_running_app()
        s = app.db.execute("SELECT date,amount FROM salaries ORDER BY id DESC LIMIT 12").fetchall()
        b = app.db.execute("SELECT date,amount FROM bonus ORDER BY id DESC LIMIT 12").fetchall()
        e = app.db.execute(
            "SELECT date,amount,category FROM expenses ORDER BY id DESC LIMIT 20").fetchall()
        lines = ["SALAIRES"]
        lines += [f"{d}  •  {money(a)}" for d, a in s] or ["Aucun salaire."]
        lines += ["\n13e MOIS"]
        lines += [f"{d}  •  {money(a)}" for d, a in b] or ["Aucun 13e mois."]
        lines += ["\nDÉPENSES"]
        lines += [f"{d}  •  {money(a)}  •  {c}" for d, a, c in e] or ["Aucune dépense."]
        self.ids.history.text = "\n".join(lines)


class SavingsScreen(Screen):
    def on_enter(self):
        self.build()

    def build(self):
        app = App.get_running_app()
        box = self.ids.content
        box.clear_widgets()
        salary = app.current_salary()
        total = app.total_saved()
        goals = app.goals()

        hero = HeroCard(size_hint_y=None, height=dp(112), bg=GREEN)
        hero.add_widget(Image(source=asset("cat_epargne"), size_hint_x=None, width=dp(96),
                              fit_mode="contain"))
        col = BoxLayout(orientation="vertical")
        col.add_widget(_left_label("Total épargne", font_size="15sp", color=WHITE))
        col.add_widget(_left_label(money(total), font_size="30sp", bold=True, color=WHITE))
        share = (f"{total / salary * 100:.0f} % de votre salaire"
                 if salary > 0 and total > 0 else "Chaque versement compte")
        col.add_widget(_left_label(share, font_size="12sp", color=(.90, 1, .94, 1)))
        hero.add_widget(col)
        box.add_widget(hero)

        planned = salary * app.budget_pct(9) / 100
        dep = app.deposits_this_month()
        pct = 0 if planned <= 0 else dep / planned * 100
        card = ChartCard()
        head = BoxLayout(size_hint_y=None, height=dp(24))
        head.add_widget(_left_label("Objectif mensuel", font_size="15sp", bold=True))
        head.add_widget(_right_label(f"{app.budget_pct(9):g} % du salaire", font_size="12sp",
                                     color=GREY))
        card.add_widget(head)
        amt = BoxLayout(size_hint_y=None, height=dp(22))
        amt.add_widget(_left_label(f"[b]{money(dep)}[/b] / {money(planned)}", markup=True,
                                   font_size="14sp"))
        amt.add_widget(_right_label(f"{pct:.0f} %", size_hint_x=None, width=dp(56), bold=True,
                                    font_size="14sp"))
        card.add_widget(amt)
        card.add_widget(HBar(fraction=min(1, pct / 100), color=GREEN, size_hint_y=None,
                             height=dp(16)))
        if salary <= 0:
            card.add_widget(wrap_label("Saisis ton salaire net pour calculer ton objectif "
                                       "d'épargne du mois.", size="12sp", color=GREY))
        else:
            card.add_widget(wrap_label(
                f"Prévu dans ton budget : {app.budget_pct(9):g} % de {money(salary)}, "
                "versé ce mois-ci.", size="12sp", color=GREY))
        planned_goals = sum(g["monthly"] for g in goals if g["saved"] < g["target"])
        if planned_goals > 0:
            extra = (" Cela dépasse ton budget d'épargne." if planned > 0 and planned_goals > planned
                     else "")
            card.add_widget(wrap_label(
                f"Versements prévus sur tes objectifs : {money(planned_goals)} par mois.{extra}",
                size="12sp", color=NEG_COLOR if extra else GREY))
        box.add_widget(card)

        grid = GridLayout(cols=2, spacing=dp(10), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        actions = (
            ("h_epargne", "Ajouter une\népargne", lambda *_: app.open_add_saving(None, "savings")),
            ("h_rapport", "Voir les\ndétails", lambda *_: setattr(app.sm, "current", "savings_details")),
            ("h_obj", "Fixer un\nobjectif", lambda *_: app.open_new_goal(None, "savings")),
            ("h_dep", "Historique", lambda *_: setattr(app.sm, "current", "savings_history")),
        )
        for src, text, cb in actions:
            tile = ActionTile(source=asset(src), text=text)
            tile.bind(on_release=cb)
            grid.add_widget(tile)
        box.add_widget(grid)

        box.add_widget(section_title("Mes différentes épargnes"))
        if not goals:
            box.add_widget(wrap_label("Aucun objectif pour l'instant. Appuie sur « Fixer un "
                                      "objectif » pour créer ton premier projet (maison, "
                                      "scolarité, véhicule, voyage...).", color=GREY))
        for g in goals:
            box.add_widget(make_goal_row(g, origin="savings"))
        free = app.free_saved()
        if abs(free) > .5:
            row = GoalRow()
            row.height = dp(76)
            row.add_widget(Image(source=asset("g_libre"), size_hint_x=None, width=dp(72),
                                 fit_mode="contain"))
            c = BoxLayout(orientation="vertical")
            c.add_widget(_left_label("Épargne libre", font_size="15sp", bold=True))
            c.add_widget(_left_label("Non affectée à un objectif", font_size="11sp", color=GREY))
            c.add_widget(_left_label(money(free), font_size="14sp", bold=True))
            row.add_widget(c)
            row.bind(on_release=lambda *_: setattr(app.sm, "current", "savings_history"))
            box.add_widget(row)


class AddSavingScreen(Screen):
    kind = StringProperty("in")
    back_to = StringProperty("savings")
    info = StringProperty("")
    preselect = None

    def __init__(self, **kw):
        super().__init__(**kw)
        self._goal_map = {}

    def set_kind(self, kind):
        self.kind = kind

    def on_enter(self):
        app = App.get_running_app()
        self._goal_map = {}
        values = ["Épargne libre"]
        for g in app.goals():
            label = g["name"]
            if label in self._goal_map or label == "Épargne libre":
                label = f"{g['name']} (#{g['id']})"
            self._goal_map[label] = g["id"]
            values.append(label)
        self.ids.goal.values = values
        selected = "Épargne libre"
        for label, gid in self._goal_map.items():
            if gid == self.preselect:
                selected = label
        self.ids.goal.text = selected
        self.ids.amount.text = ""
        self.ids.note.text = ""
        self.ids.date.text = dt_date.today().strftime("%d-%m-%Y")
        self.kind = "in"
        self.preselect = None
        self.update_info()

    def _goal_id(self):
        return self._goal_map.get(self.ids.goal.text)

    def update_info(self):
        app = App.get_running_app()
        if app.db is None:
            return
        gid = self._goal_id()
        bal = app.saved_for(gid)
        if gid is None:
            self.info = f"Solde de l'épargne libre : {money(bal)}"
        else:
            g = app.goal(gid)
            rest = max(0, g["target"] - g["saved"]) if g else 0
            self.info = f"Déjà réuni : {money(bal)}   •   reste à financer : {money(rest)}"

    def save(self):
        app = App.get_running_app()
        try:
            amount = float(self.ids.amount.text or 0)
        except ValueError:
            amount = 0
        if amount <= 0:
            popup("Montant invalide", "Saisis un montant supérieur à 0.")
            return
        text_date = self.ids.date.text.strip()
        d = parse_date(text_date) if text_date else dt_date.today()
        if d is None:
            popup("Date invalide", "Utilise le format JJ-MM-AAAA.\nExemple : 05-10-2026.")
            return
        gid = self._goal_id()
        if self.kind == "out":
            bal = app.saved_for(gid)
            if amount > bal + .01:
                popup("Solde insuffisant", f"Tu ne peux retirer que {money(bal)}\nde cette épargne.",
                      size=(.85, .3))
                return
            signed = -amount
        else:
            signed = amount
        app.db.execute("INSERT INTO savings(date,amount,goal_id,note) VALUES(?,?,?,?)",
                       (d.isoformat(), signed, gid, self.ids.note.text.strip()))
        app.db.commit()
        msg = (f"Versement de {money(amount)} enregistré." if signed > 0
               else f"Retrait de {money(amount)} enregistré.")
        if gid is not None:
            g = app.goal(gid)
            if g and signed > 0 and g["saved"] >= g["target"]:
                msg += "\nObjectif atteint, bravo !"
        popup("Épargne enregistrée", msg, size=(.85, .3))
        app.sm.current = self.back_to


class SavingsHistoryScreen(Screen):
    def on_enter(self):
        self.build()

    def build(self):
        app = App.get_running_app()
        box = self.ids.content
        box.clear_widgets()
        ins, outs = app.db.execute(
            "SELECT COALESCE(SUM(CASE WHEN amount>0 THEN amount END),0),"
            " COALESCE(SUM(CASE WHEN amount<0 THEN -amount END),0) FROM savings").fetchone()
        card = ChartCard()
        card.add_widget(kv_row("Total des versements", money(ins), color=POS_COLOR))
        card.add_widget(kv_row("Total des retraits", money(outs), color=NEG_COLOR))
        card.add_widget(kv_row("Solde restant", money(ins - outs)))
        box.add_widget(card)
        entries = app.db.execute(
            "SELECT s.id,s.date,s.amount,s.note,g.name FROM savings s "
            "LEFT JOIN goals g ON g.id=s.goal_id ORDER BY s.date DESC, s.id DESC LIMIT 100"
        ).fetchall()
        if not entries:
            box.add_widget(wrap_label("Aucun versement enregistré pour l'instant.", color=GREY))
        for sid, d, amount, note, gname in entries:
            row = RowCard()
            col = BoxLayout(orientation="vertical")
            col.add_widget(_left_label(gname or "Épargne libre", font_size="13sp", bold=True,
                                       shorten=True))
            dd = parse_date(d)
            sub = fmt_date(dd) if dd else str(d)
            if note:
                sub += f"  •  {note}"
            col.add_widget(_left_label(sub, font_size="11sp", color=GREY, shorten=True))
            row.add_widget(col)
            positive = amount >= 0
            row.add_widget(_right_label(
                ("+ " + money(amount)) if positive else ("- " + money(-amount)),
                font_size="14sp", bold=True, size_hint_x=None, width=dp(104),
                color=POS_COLOR if positive else NEG_COLOR))
            btn = Button(text="×", font_size="22sp", size_hint_x=None, width=dp(34),
                         background_color=(0, 0, 0, 0), color=NEG_COLOR)
            btn.bind(on_release=lambda *_, i=sid: self.ask_delete(i))
            row.add_widget(btn)
            box.add_widget(row)

    def ask_delete(self, sid):
        confirm("Supprimer ce mouvement ?",
                "Il sera retiré de l'historique et des soldes.", lambda: self.delete(sid),
                yes_text="Supprimer", no_text="Annuler")

    def delete(self, sid):
        app = App.get_running_app()
        app.db.execute("DELETE FROM savings WHERE id=?", (sid,))
        app.db.commit()
        self.build()


class SavingsDetailsScreen(Screen):
    def on_enter(self):
        self.build()

    def build(self):
        app = App.get_running_app()
        box = self.ids.content
        box.clear_widgets()
        today = dt_date.today()
        months = []
        for k in range(5, -1, -1):
            idx = today.month - 1 - k
            months.append((today.year + idx // 12, idx % 12 + 1))
        sums = {r[0]: r[1] for r in app.db.execute(
            "SELECT substr(date,1,7), SUM(amount) FROM savings GROUP BY 1").fetchall()}
        vals = [sums.get(f"{y:04d}-{m:02d}", 0) or 0 for y, m in months]
        count = app.db.execute("SELECT COUNT(*) FROM savings").fetchone()[0]

        card = ChartCard()
        card.add_widget(section_title("Résumé"))
        card.add_widget(kv_row("Total épargné", money(app.total_saved())))
        card.add_widget(kv_row("Ce mois-ci (net)", money(vals[-1])))
        card.add_widget(kv_row("Moyenne sur 6 mois", money(sum(vals) / 6)))
        card.add_widget(kv_row("Nombre de mouvements", str(count)))
        box.add_widget(card)

        card = ChartCard()
        card.add_widget(section_title("Évolution mensuelle"))
        top = max(vals) if vals else 0
        if top <= 0:
            card.add_widget(wrap_label("Enregistre des versements pour voir l'évolution.",
                                       color=GREY))
        else:
            cols = BoxLayout(size_hint_y=None, height=dp(170), spacing=dp(2))
            for (y, m), v in zip(months, vals):
                c = BoxLayout(orientation="vertical")
                lab = f"{v / 1000:.0f}k" if abs(v) >= 1000 else f"{v:.0f}"
                c.add_widget(Label(text=lab, font_size="11sp", bold=True, size_hint_y=None,
                                   height=dp(18)))
                c.add_widget(VBar(fraction=max(0, v) / top, color=GREEN))
                c.add_widget(Label(text=f"{m:02d}/{y % 100:02d}", font_size="11sp",
                                   size_hint_y=None, height=dp(18), color=GREY))
                cols.add_widget(c)
            card.add_widget(cols)
        box.add_widget(card)

        card = ChartCard()
        card.add_widget(section_title("Par objectif"))
        goals = app.goals()
        if not goals:
            card.add_widget(wrap_label("Aucun objectif créé.", color=GREY))
        for g in goals:
            pct = pct_of(g["saved"], g["target"])
            card.add_widget(bar_row(g["name"], f"{pct:.0f} %", pct / 100, GREEN))
            proj = projected_date(g)
            rest = max(0, g["target"] - g["saved"])
            if rest <= 0:
                tail = "objectif atteint"
            elif proj:
                tail = f"atteint vers {fmt_month(proj)}"
            else:
                tail = "date non estimée"
            card.add_widget(wrap_label(
                f"{money(g['saved'])} sur {money(g['target'])}  •  reste {money(rest)}  •  {tail}",
                size="11sp", color=GREY))
        free = app.free_saved()
        if abs(free) > .5:
            card.add_widget(kv_row("Épargne libre", money(free)))
        box.add_widget(card)


class GoalsScreen(Screen):
    def on_enter(self):
        self.build()

    def build(self):
        app = App.get_running_app()
        box = self.ids.content
        box.clear_widgets()
        goals = app.goals()

        banner = HeroCard(size_hint_y=None, height=dp(112), bg=[.87, .96, .89, 1])
        banner.add_widget(Image(source=asset("h_obj"), size_hint_x=None, width=dp(84),
                                fit_mode="contain"))
        col = BoxLayout(orientation="vertical")
        col.add_widget(_left_label("Vos projets, notre priorité !", font_size="17sp", bold=True,
                                   color=(.03, .30, .17, 1)))
        col.add_widget(_left_label("Planifiez aujourd'hui, réalisez demain.", font_size="12sp",
                                   color=(.20, .35, .28, 1)))
        banner.add_widget(col)
        box.add_widget(banner)

        btn = Factory.PrimaryButton(text="+  Créer un nouvel objectif")
        btn.bind(on_release=lambda *_: app.open_new_goal(None, "goals"))
        box.add_widget(btn)

        active = [g for g in goals if g["saved"] < g["target"]]
        total_target = sum(g["target"] for g in goals)
        total_done = sum(min(g["saved"], g["target"]) for g in goals)
        rate = total_done / total_target * 100 if total_target > 0 else 0
        dues = [months_left(g["due"]) for g in active if g["due"]]
        if not dues:
            nearest = "—"
        else:
            m = min(dues)
            nearest = "Dépassée" if m < 0 else ("Ce mois-ci" if m == 0 else f"{m} mois")
        grid = GridLayout(cols=2, spacing=dp(8), size_hint_y=None)
        grid.bind(minimum_height=grid.setter("height"))
        for title, value, src, bg, fg in (
            ("Objectifs actifs", str(len(active)), "s_actifs", [.89, .98, .92, 1], [.02, .42, .18, 1]),
            ("Montant total", money(total_target), "s_montant", [.88, .94, 1, 1], [.04, .30, .60, 1]),
            ("Échéance la plus proche", nearest, "s_echeance", [1, .94, .86, 1], [.75, .35, 0, 1]),
            ("Taux de réalisation", f"{rate:.0f} %", "s_taux", [.93, .90, 1, 1], [.38, .18, .68, 1]),
        ):
            grid.add_widget(StatIcon(title=title, value=value, source=asset(src), bg=bg, fg=fg))
        box.add_widget(grid)

        box.add_widget(section_title("Mes objectifs"))
        if not goals:
            box.add_widget(wrap_label("Aucun objectif pour l'instant. Crée ton premier projet : "
                                      "maison, voiture, études, voyage...", color=GREY))
        for g in goals:
            box.add_widget(make_goal_row(g, show_due=True, show_tag=True, origin="goals"))

        quote = HeroCard(size_hint_y=None, height=dp(52), bg=[.89, .94, 1, 1])
        quote.add_widget(wrap_label("« Chaque objectif atteint est une victoire sur soi. »",
                                    size="12sp", halign="center", color=(.06, .30, .55, 1)))
        box.add_widget(quote)


class NewGoalScreen(Screen):
    back_to = StringProperty("goals")
    title_text = StringProperty("Nouvel objectif")
    priority = StringProperty("Normale")
    icon = StringProperty("maison")
    edit_id = None

    def on_enter(self):
        app = App.get_running_app()
        g = app.goal(self.edit_id) if self.edit_id else None
        ids = self.ids
        if g:
            self.title_text = "Modifier l'objectif"
            ids.name.text = g["name"]
            ids.note.text = g["note"]
            ids.target.text = f"{g['target']:.0f}"
            ids.due.text = g["due"].strftime("%d-%m-%Y") if g["due"] else ""
            ids.monthly.text = f"{g['monthly']:.0f}" if g["monthly"] else ""
            self.priority = g["priority"]
            self.icon = g["icon"]
        else:
            self.title_text = "Nouvel objectif"
            for k in ("name", "note", "target", "due", "monthly"):
                ids[k].text = ""
            self.priority = "Normale"
            self.icon = "maison"
        self.build_icons()

    def build_icons(self):
        box = self.ids.icons
        box.clear_widgets()
        for key, label in GOAL_ICONS:
            pick = IconPick(source=asset("g_" + key), text=label, selected=(key == self.icon))
            pick.bind(on_release=lambda w, k=key, l=label: self.pick(k, l))
            box.add_widget(pick)

    def pick(self, key, label):
        prev = dict(GOAL_ICONS).get(self.icon, "")
        current = self.ids.name.text.strip()
        if not current or current == prev:
            self.ids.name.text = label
        self.icon = key
        self.build_icons()

    def save(self):
        app = App.get_running_app()
        ids = self.ids
        name = ids.name.text.strip()
        if not name:
            popup("Nom manquant", "Donne un nom à ton projet.")
            return
        try:
            target = float(ids.target.text or 0)
        except ValueError:
            target = 0
        if target <= 0:
            popup("Montant invalide", "Saisis le montant à atteindre.")
            return
        due = None
        if ids.due.text.strip():
            due = parse_date(ids.due.text)
            if due is None:
                popup("Date invalide", "Utilise le format JJ-MM-AAAA.\nExemple : 31-12-2027.")
                return
        try:
            monthly = max(0, float(ids.monthly.text or 0))
        except ValueError:
            monthly = 0
        values = (name, ids.note.text.strip(), target, due.isoformat() if due else "",
                  self.priority, monthly, self.icon)
        editing = bool(self.edit_id)
        if editing:
            app.db.execute("UPDATE goals SET name=?,note=?,target=?,due_date=?,priority=?,"
                           "monthly=?,icon=? WHERE id=?", values + (self.edit_id,))
        else:
            app.db.execute("INSERT INTO goals(name,note,target,due_date,priority,monthly,icon,"
                           "created) VALUES(?,?,?,?,?,?,?,?)",
                           values + (dt_date.today().isoformat(),))
        app.db.commit()
        popup("Objectif enregistré", f"« {name} » : {money(target)}")
        app.sm.current = self.back_to if editing else "goals"


class GoalDetailScreen(Screen):
    back_to = StringProperty("goals")
    goal_id = None

    def on_enter(self):
        self.build()

    def build(self):
        app = App.get_running_app()
        box = self.ids.content
        box.clear_widgets()
        g = app.goal(self.goal_id)
        if g is None:
            app.sm.current = "goals"
            return
        pct = pct_of(g["saved"], g["target"])
        rest = max(0, g["target"] - g["saved"])

        card = ChartCard()
        head = BoxLayout(size_hint_y=None, height=dp(96), spacing=dp(12))
        head.add_widget(Image(source=asset("g_" + g["icon"]), size_hint_x=None, width=dp(128),
                              fit_mode="contain"))
        info = BoxLayout(orientation="vertical", spacing=dp(2))
        info.add_widget(_left_label(g["name"], font_size="20sp", bold=True))
        info.add_widget(_left_label(g["note"] or " ", font_size="12sp", color=GREY))
        tag_row = BoxLayout(size_hint_y=None, height=dp(26))
        bg, fg = PRIORITY_STYLE.get(g["priority"], PRIORITY_STYLE["Normale"])
        tag_row.add_widget(Tag(text="Priorité " + g["priority"].lower(), bg=bg, fg=fg,
                               pos_hint={"center_y": .5}))
        tag_row.add_widget(Widget())
        info.add_widget(tag_row)
        head.add_widget(info)
        card.add_widget(head)
        amounts = BoxLayout(size_hint_y=None, height=dp(24))
        amounts.add_widget(_left_label(f"[b]{money(g['saved'])}[/b] / {money(g['target'])}",
                                       markup=True, font_size="15sp"))
        amounts.add_widget(_right_label(f"{pct:.0f} %", size_hint_x=None, width=dp(56),
                                        font_size="15sp", bold=True))
        card.add_widget(amounts)
        card.add_widget(HBar(fraction=pct / 100, color=GREEN, size_hint_y=None, height=dp(16)))
        box.add_widget(card)

        card = ChartCard()
        card.add_widget(kv_row("Déjà réuni", money(g["saved"]), color=POS_COLOR))
        card.add_widget(kv_row("Reste à financer", money(rest)))
        due = g["due"]
        card.add_widget(kv_row("Échéance", (fmt_date(due) + "  (" + months_text(due) + ")")
                               if due else "Non définie"))
        card.add_widget(kv_row("Épargne mensuelle prévue",
                               money(g["monthly"]) if g["monthly"] else "Non définie"))
        proj = projected_date(g)
        if rest <= 0:
            card.add_widget(kv_row("Statut", "Objectif atteint", color=POS_COLOR))
        else:
            card.add_widget(kv_row("Date prévisionnelle", fmt_month(proj) if proj else "—"))
            req = required_monthly(g)
            if req is not None:
                if months_left(due) == -1:
                    advice = ("L'échéance est dépassée : modifie la date souhaitée ou accélère "
                              "tes versements.")
                elif g["monthly"] >= req:
                    advice = "Ton épargne mensuelle prévue suffit pour tenir l'échéance."
                elif proj and due and proj > due:
                    advice = (f"À ce rythme, l'objectif sera atteint en {fmt_month(proj)}, après "
                              f"l'échéance. Pour la tenir, épargne environ {money(req)} par mois.")
                else:
                    advice = f"Pour tenir l'échéance, épargne environ {money(req)} par mois."
                card.add_widget(wrap_label(advice, size="12sp", color=(.04, .32, .62, 1)))
            elif not g["monthly"]:
                card.add_widget(wrap_label("Définis une épargne mensuelle (bouton Modifier) pour "
                                           "estimer la date d'atteinte.", size="12sp", color=GREY))
        box.add_widget(card)

        recent = app.db.execute(
            "SELECT date,amount,note FROM savings WHERE goal_id=? ORDER BY date DESC, id DESC "
            "LIMIT 5", (g["id"],)).fetchall()
        card = ChartCard()
        card.add_widget(section_title("Derniers versements"))
        if not recent:
            card.add_widget(wrap_label("Aucun versement pour cet objectif.", color=GREY))
        for d, a, n in recent:
            dd = parse_date(d)
            label = (fmt_date(dd) if dd else str(d)) + (f"  •  {n}" if n else "")
            card.add_widget(kv_row(label, ("+ " + money(a)) if a >= 0 else ("- " + money(-a)),
                                   color=POS_COLOR if a >= 0 else NEG_COLOR))
        box.add_widget(card)

        add = Factory.PrimaryButton(text="Ajouter un versement")
        add.bind(on_release=lambda *_: app.open_add_saving(g["id"], "goal_detail"))
        box.add_widget(add)
        edit = Button(text="Modifier l'objectif", size_hint_y=None, height=dp(48))
        edit.bind(on_release=lambda *_: app.open_new_goal(g["id"], "goal_detail"))
        box.add_widget(edit)
        delete = Button(text="Supprimer l'objectif", size_hint_y=None, height=dp(48),
                        background_color=(1, .90, .90, 1), color=NEG_COLOR)
        delete.bind(on_release=lambda *_: self.ask_delete(g))
        box.add_widget(delete)

    def ask_delete(self, g):
        confirm("Supprimer cet objectif ?",
                f"« {g['name']} » sera supprimé.\nLes {money(g['saved'])} épargnés passent en "
                "épargne libre.", lambda: self.delete(g["id"]),
                yes_text="Supprimer", no_text="Annuler")

    def delete(self, gid):
        app = App.get_running_app()
        app.db.execute("UPDATE savings SET goal_id=NULL WHERE goal_id=?", (gid,))
        app.db.execute("DELETE FROM goals WHERE id=?", (gid,))
        app.db.commit()
        app.sm.current = "goals"


class ResetScreen(Screen):
    def on_enter(self):
        self.build()

    def build(self):
        app = App.get_running_app()
        box = self.ids.content
        box.clear_widgets()
        warn = HeroCard(size_hint_y=None, height=dp(86), bg=[1, .93, .93, 1])
        warn.add_widget(wrap_label(
            "Attention : une remise à zéro est définitive. Chaque action demande une "
            "confirmation. Les autres données ne sont pas touchées.", size="13sp",
            color=NEG_COLOR))
        box.add_widget(warn)
        for kind in RESET_ORDER + ["all"]:
            title, desc = RESETS[kind]
            card = ChartCard()
            head = BoxLayout(size_hint_y=None, height=dp(26))
            head.add_widget(_left_label(title, font_size="15sp", bold=True))
            head.add_widget(_right_label(app.reset_info(kind), font_size="12sp", color=GREY,
                                         shorten=True))
            card.add_widget(head)
            card.add_widget(wrap_label(desc, size="12sp", color=GREY))
            if kind == "all":
                btn = Button(text="Tout remettre à zéro", size_hint_y=None, height=dp(46),
                             background_color=(.80, .15, .15, 1), color=WHITE)
            else:
                btn = Factory.DangerButton(text="Remettre à zéro")
            btn.bind(on_release=lambda *_, k=kind: app.ask_reset(k, self.build))
            card.add_widget(btn)
            box.add_widget(card)


class MonSalaireApp(App, DBMixin):
    title = "MON SALAIRE"

    def build(self):
        self.sm = ScreenManager()
        self.db = None
        Builder.load_string(KV.replace("@@", ASSETS))
        self.sm.add_widget(StartupScreen(name="startup"))
        for name, cls in (
            ("home", HomeScreen), ("salary", SalaryScreen),
            ("budget", BudgetScreen), ("food", FoodScreen), ("expenses", ExpensesScreen),
            ("shopping", ShoppingScreen),
            ("bonus", BonusScreen), ("commitments", CommitmentsScreen),
            ("reports", ReportsScreen), ("history", HistoryScreen),
            ("savings", SavingsScreen), ("savings_history", SavingsHistoryScreen),
            ("savings_details", SavingsDetailsScreen), ("add_saving", AddSavingScreen),
            ("goals", GoalsScreen), ("new_goal", NewGoalScreen),
            ("goal_detail", GoalDetailScreen), ("reset", ResetScreen),
        ):
            self.sm.add_widget(cls(name=name))
        self.sm.current = "startup"
        self._menu = None
        Window.bind(on_keyboard=self.on_back_key)
        return self.sm

    def on_back_key(self, window, key, *args):
        """Bouton Retour du telephone : revient en arriere au lieu de quitter."""
        if key == 27:
            if self._menu is not None:
                self._menu.dismiss()
                return True
            current = self.sm.current
            if current in ("home", "startup"):
                return False  # laisse Android quitter l'application
            screen = self.sm.current_screen
            target = getattr(screen, "back_to", None) or SCREEN_PARENTS.get(current, "home")
            self.sm.current = target
            return True
        return False

    def startup(self):
        screen = self.sm.get_screen("startup")
        try:
            screen.ids.status.text = "Vérification de la base de données..."
            self.init_db()
            screen.ids.checks.text = "OK - Base de données\n"
            screen.ids.status.text = "Vérification de l'interface..."
            required = ["home", "salary", "budget", "food", "expenses", "bonus",
                        "commitments", "reports", "history", "savings", "savings_history",
                        "savings_details", "add_saving", "goals", "new_goal", "goal_detail",
                        "reset"]
            missing = [x for x in required if x not in self.sm.screen_names]
            if missing:
                raise RuntimeError("Écrans non chargés : " + ", ".join(missing))
            screen.ids.checks.text += "OK - Accueil, budget, alimentation, dépenses,\n13e mois, scolarité / prêts, historique"
            screen.ids.status.text = "Prêt."
            screen.ids.retry.disabled = True
            from kivy.clock import Clock
            Clock.schedule_once(lambda dt: setattr(self.sm, "current", "home"), .4)
        except Exception as exc:
            screen.ids.status.text = "Problème au démarrage"
            screen.ids.checks.text = f"Erreur : {type(exc).__name__}: {exc}\n\nAppuie sur « Réessayer »."
            screen.ids.retry.disabled = False

    # ----- menu lateral et remise a zero -----
    def open_menu(self):
        if self._menu is not None:
            return
        self._menu = SideMenu(self)
        self._menu.open()

    def close_menu(self):
        if self._menu is not None:
            self._menu.dismiss()

    def reset_info(self, kind):
        q = lambda sql: self.db.execute(sql).fetchone()[0]  # noqa: E731
        if kind == "expenses":
            return plural(q("SELECT COUNT(*) FROM expenses"), "dépense")
        if kind == "salary":
            return plural(q("SELECT COUNT(*) FROM salaries"), "salaire")
        if kind == "bonus":
            return plural(q("SELECT COUNT(*) FROM bonus"), "montant")
        if kind == "savings":
            return plural(q("SELECT COUNT(*) FROM savings"), "mouvement")
        if kind == "goals":
            return plural(q("SELECT COUNT(*) FROM goals"), "objectif")
        if kind == "commitments":
            return plural(q("SELECT COUNT(*) FROM schooling") + q("SELECT COUNT(*) FROM loans"),
                          "élément")
        if kind in ("budget", "budget_pct", "food"):
            changed = 0
            if kind in ("budget", "budget_pct"):
                changed += sum(1 for i, d in enumerate(DEFAULT_BUDGET)
                               if abs(self.budget_pct(i) - d[2]) > 1e-9)
            if kind in ("budget", "food"):
                changed += sum(1 for i, d in enumerate(FOOD_DEFAULT)
                               if abs(self.food_amount(i) - d[2]) > 1e-9)
            return plural(changed, "valeur") + " modifiée" + ("s" if changed > 1 else "")
        return "Toutes les données"

    def _reset_settings(self, prefix, defaults):
        self.db.execute("DELETE FROM settings WHERE substr(key,1,?)=?", (len(prefix), prefix))
        for i, d in enumerate(defaults):
            self.db.execute("INSERT OR REPLACE INTO settings(key,value) VALUES(?,?)",
                            (f"{prefix}{i}", str(d[2])))

    def reset_data(self, kind):
        db = self.db
        kinds = RESET_ORDER if kind == "all" else [kind]
        for k in kinds:
            if k == "expenses":
                db.execute("DELETE FROM expenses")
            elif k == "salary":
                db.execute("DELETE FROM salaries")
            elif k == "bonus":
                db.execute("DELETE FROM bonus")
            elif k == "savings":
                db.execute("DELETE FROM savings")
            elif k == "goals":
                db.execute("UPDATE savings SET goal_id=NULL")
                db.execute("DELETE FROM goals")
            elif k == "commitments":
                db.execute("DELETE FROM schooling")
                db.execute("DELETE FROM loans")
            elif k in ("budget", "budget_pct", "food"):
                if k in ("budget", "budget_pct"):
                    self._reset_settings("pct_", DEFAULT_BUDGET)
                if k in ("budget", "food"):
                    self._reset_settings("food_", FOOD_DEFAULT)
        db.commit()

    def ask_reset(self, kind, after=None):
        title, desc = RESETS[kind]

        def do():
            self.reset_data(kind)
            popup("Remise à zéro effectuée", f"{title} : données remises à zéro.",
                  size=(.85, .28))
            if after:
                after()

        if kind == "all":
            def second():
                confirm("Dernière confirmation",
                        "Toutes tes données seront définitivement perdues.\nContinuer ?",
                        do, yes_text="Tout effacer", no_text="Annuler")
            confirm("Tout remettre à zéro ?", desc, second, yes_text="Continuer",
                    no_text="Annuler")
        else:
            confirm(f"Remettre à zéro : {title} ?", desc + "\nCette action est définitive.",
                    do, yes_text="Remettre à zéro", no_text="Annuler")

    # ----- epargne et objectifs -----
    def goals(self):
        rows = self.db.execute(
            "SELECT g.id,g.name,g.note,g.target,g.due_date,g.priority,g.monthly,g.icon,"
            " COALESCE((SELECT SUM(amount) FROM savings s WHERE s.goal_id=g.id),0)"
            " FROM goals g").fetchall()
        out = []
        for r in rows:
            out.append({"id": r[0], "name": r[1], "note": r[2] or "", "target": float(r[3] or 0),
                        "due": parse_date(r[4]), "priority": r[5] or "Normale",
                        "monthly": float(r[6] or 0), "icon": r[7] or "projet",
                        "saved": float(r[8] or 0)})
        out.sort(key=lambda g: (PRIORITY_RANK.get(g["priority"], 1), g["due"] or dt_date.max,
                                g["id"]))
        return out

    def goal(self, gid):
        return next((g for g in self.goals() if g["id"] == gid), None)

    def total_saved(self):
        return float(self.db.execute("SELECT COALESCE(SUM(amount),0) FROM savings").fetchone()[0])

    def free_saved(self):
        return self.saved_for(None)

    def saved_for(self, gid):
        if gid is None:
            q = self.db.execute("SELECT COALESCE(SUM(amount),0) FROM savings WHERE goal_id IS NULL")
        else:
            q = self.db.execute("SELECT COALESCE(SUM(amount),0) FROM savings WHERE goal_id=?",
                                (gid,))
        return float(q.fetchone()[0])

    def deposits_this_month(self):
        first = dt_date.today().replace(day=1).isoformat()
        return float(self.db.execute(
            "SELECT COALESCE(SUM(amount),0) FROM savings WHERE amount>0 AND date>=?",
            (first,)).fetchone()[0])

    def open_add_saving(self, goal_id=None, origin="savings"):
        screen = self.sm.get_screen("add_saving")
        screen.preselect = goal_id
        screen.back_to = origin
        self.sm.current = "add_saving"

    def open_new_goal(self, goal_id=None, origin="goals"):
        screen = self.sm.get_screen("new_goal")
        screen.edit_id = goal_id
        screen.back_to = origin
        self.sm.current = "new_goal"

    def open_goal(self, goal_id, origin="goals"):
        screen = self.sm.get_screen("goal_detail")
        screen.goal_id = goal_id
        screen.back_to = origin
        self.sm.current = "goal_detail"

    def current_salary(self):
        row = self.db.execute("SELECT amount FROM salaries ORDER BY id DESC LIMIT 1").fetchone()
        return float(row[0]) if row else 0

    def total_expenses(self):
        return float(self.db.execute("SELECT COALESCE(SUM(amount),0) FROM expenses").fetchone()[0])

    def monthly_commitments(self):
        school = float(self.db.execute("SELECT COALESCE(SUM(monthly),0) FROM schooling").fetchone()[0])
        loans = float(self.db.execute("SELECT COALESCE(SUM(monthly_payment),0) FROM loans").fetchone()[0])
        return school + loans

    def budget_pct(self, i):
        return self.setting(f"pct_{i}", DEFAULT_BUDGET[i][2])

    def food_amount(self, i):
        return self.setting(f"food_{i}", FOOD_DEFAULT[i][2])


if __name__ == "__main__":
    MonSalaireApp().run()
