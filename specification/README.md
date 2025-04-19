# crazystockbadges
Crazy Stock Badges Project


# Project Proposal

CC Project Proposal:  ‘Crazy Stock Badges’
Martin East (mbe5)

## Project Description
This is an exploration of computational creativity in 3-D modelling using financial data. Electronic stock exchanges, such as the London Stock Exchange, hold public structured data that abstractly describe the value and behaviour of incorporated businesses. By definition, the act of incorporation treats these entities as a person. They engage in activities like making things, delivering services, owning land, employing people, paying tax, they also exhibit emotion, conflict, success, and failure. These are captured in large volumes of numeric data. Analysis on this data is carried out routinely by Banks, and trading funds for profit. 

This project aims to capture this abstract data and re-work it into a 3-D model which can be printed into a physical object, a badge. The computer program I will write will do this autonomously and add a ‘crazy’ element, perhaps this is just direct from the market, or maybe it is added in by the algorithm, either way the idea is to produce a physical manifestation of the data.

## Methodology
The input will be time series financial data for a given stock (e.g daily closing prices for Apple Inc for the last year). It will be processed with some machine algorithms. The output will be a multi dimensional dataset, that conveys texture and shape. This data will be applied to a templated 3-D model (STL file) using a python library such as Pymesh [3]. Finally the STL model will be viewed in a tool such as Blender, and hopefully printed in the HackSpace on campus using PrusaSlicer software.

## Links to creativity
The creation of an artifact from numeric financial data will be a novel and visceral experience, for example a Tesla stock price dropping may create a sharp edge, or spiky texture that can be felt and seen. It is an exploration of the transformation of real world events, to abstract numbers, and then back into the world. The information is abstracted, passed through multiple systems and ends up in our hands as a static historic snapshot. I’m interested if this will successfully convey a story behind the numbers.

## Background 
Basic market data is publicly available data available through an API at Yahoo finance (yfinance) [1]. Fast fourier transforms [4] or other machine learning techniques may pick out interesting patterns. SP-GAN may be an architecture that can be used for generating a 3-D model [2]. Pymesh is a library able to generate STL files [3]. The hyperparameters and stochastic nature of the algorithm’s will hopefully add surprise.

## Evaluation
 I expect to evaluate the way the program processes data to combine two conceptual spaces (finance data and 3-D art). I hope it will make intriguing and pleasing results, although they are unlikely to shock. It is quite possible the algorithm will not exhibit true process creativity. The 4-P’s of Product, Process, Producer and Press/Environment [7], and FACE (Frame, Aesthetic measure, Concept, and Example/expression) [6], will be two frameworks to apply, as we have a clear process and artefact to assess.
 
## Reference list
[1] Aroussi, R. (2023). yfinance: Yahoo! Finance market data downloader. [online] PyPI. Available at: https://pypi.org/project/yfinance/.
[2] Li, R., Li, X., Hui, K.-H. and Fu, C.-W. (2021). SP-GAN. ACM Transactions on Graphics, 40(4), pp.1–12. doi:https://doi.org/10.1145/3450626.3459766.
[3] pymesh.readthedocs.io. (n.d.). PyMesh — Geometry Processing Library for Python — PyMesh 0.2.1 documentation. [online] Available at: https://pymesh.readthedocs.io/en/latest/.
[4] Wikipedia Contributors (2019). Fast Fourier transform. [online] Wikipedia. Available at: https://en.wikipedia.org/wiki/Fast_Fourier_transform.
[6] Pease, A. and Colton, S., 2011, December. Computational Creativity Theory: Inspirations behind the FACE and the IDEA models. In ICCC (pp. 72-77).
[7] Jordanous, A. (2016). Four PPPPerspectives on computational creativity in theory and in practice. Connection Science, 28(2), 194–216. https://doi.org/10.1080/09540091.2016.1151860


# Specification Overview

The objective is to consume stock market data for a given symbol ticker, and generate a 3-D STL file from it, that can then be printed. A genetic algorithm will add stochasiticity to the process, within constraints. 

## Technology choice
The program will be written in PYTHON.
The market data will come from YFINANCE.
We will use OpenSCAD via Solid Python library.
Openrouter.ai will be used for the LLM Stock Report.
pyGAD will be the genetic algorithm.
The program will be command line driven.

## Use case

User input is denoted with the right chevron (>).

'''
./crazystockbadge
Hi, welcome to crazy stock badge generator, are you ready to get crazy? What stock price symbol would you like to choose?

> TSLA

Ok, you chose APPL. Let's see what we can do.
... Retrieving Market Data from Yahoo Finance
... Running some technical Analysis
...   1 Year High/Low = 123/156
...   Latest MACD = -4
... Generating a market report, would you like to see it?

> Yes
Welcome to the financial news segment, where we bring you the latest updates and insights on the world of business. Today, let's talk about one of the most talked about stocks in the market - Tesla (TSLA).

Tesla has been making headlines since its inception, but it was the past year that truly put the company on the spotlight. Despite facing challenges such as production issues and CEO Elon Musk's controversial tweets, Tesla managed to turn a profit for the first time in its history.

But what's more impressive is Tesla's vision for the future. The company has been revolutionizing the automotive industry with its cutting-edge electric cars and has disrupted the energy sector with its solar panels and batteries. Not to mention, Tesla's autopilot technology is paving the way for self-driving cars.

In terms of pricing, TSLA has had a rocky journey. After hitting a record high of $900 in January 2021, the stock experienced a dip due to the global chip shortage and safety concerns. However, with the recent surge in demand for electric cars and strong financial performance, Tesla's stock has bounced back and is currently trading at around $700.

Looking ahead, Tesla is poised for even more growth. The company is expanding its presence in international markets, with the opening of a Gigafactory in China and plans for a factory in Germany. Plus, with its focus on renewable energy and sustainability, Tesla is well-positioned for the growing demand for clean energy solutions.

In conclusion, Tesla's past, present, and future are all intertwined with innovation, disruption, and success. And as we continue to monitor this stock's performance, it's clear that TSLA is a company worth keeping an eye on. This concludes our report, thank you for tuning in.


... Starting the 3-D badge generation...
... Choosing one that's crazy, running GA with 100 generations...
... OK I found one, writing to scad file...
...    Size = 
...    No. of objects = 
...    Height difference (Z) = 
...    Width difference (X) = 
...    Depth difference (Y) = 

'''

## Code Design blocks

Description of the overall code design blocks
   * Command Line Interface 
   * Gather Data
   * Make Model
   * Render

### Command Line Interface

Using Argparse, create a simple interface that asks questions and answers, and some friendly output as described in the Use Case above.



### Gather Data

INPUT: stock ticker symbol
OUTPUT: market data CSV, stock report and sentiment analysis number. 

This block handles the gathering of the market data and the technical analysis used by the model generator.
  * Get Market Data: gather market data for the input symbol from yfinance, 1 year of data.
  * Technical analysis: Get moving averages and MACD for the data.
  * Get Stock report: Use Openrouter.ai to prompt for a stock report, make it short 200 works and light hearted, as if done by a passionate presenter of a tv program  
  * Write the data and the report to files, data in CSV format.

### Generate Model

INPUT = market data, stock report

Using a pool of known starter shapes build a SCAD model with SolidPython, create a suitable representation of the model in GenPY, and run 100 iterations of the algorithm, evaluating it with a fitness function. The output is a SCAD file written to disk.

### Pool of designs database

Each model starts with a Base, has a Feature applied to it, and finally Text applied.

BASE: Round disc, Rectangle, Triangle
FEATURE: Spiral design with stock price plotted on the spiral, Grid design, with stock price plotted on a grid pattern.
TEXT: Ticker symbol, Price high and lows, One Word sentiment analysis.

### Model object

The model contains the following items: 
 * Individual representation:
    - Base
    - Feature
    - Text

    - No. of objects 
    - The min/max height
    - min/max Depth
    - min/max width
    - Scaling Factor (MACD)
 * SCAD SolidPython Model

 * Generate model function
   This builds the SCAN Solid Python Model using the BASE, FEature, Text and Scaling Factor, and puts it into the SCAD SolidPython Model part of the object

* Fitness function
    A fitness function that uses the following formula:
    No. of objects * Scaling Factor + Depth difference + Width Difference + Height Difference.
    With maximisation desirable.

### Choosing a design

Execute a GENPY genetic algorithm over 100 iterations to find a 'crazy' design, using the fitness and generate functions above.


### Render

A render object/class that creates the SCAD file and writes it to the object and to disk. This may later be extended to visualise the object on screen.
