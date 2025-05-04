# Logical Flow Diagram of Crazy Stock Badges Code

This document provides a logical flow diagram that shows how the different components of the Crazy Stock Badges project interact and the overall program flow. The project is a system that generates 3D printable badges based on stock market data, with sentiment analysis and complexity metrics.

## High-Level Architecture

```mermaid
graph TD
    A[Main CLI - CrazyStockBadge] --> B[MarketDataManager]
    A --> C[BadgeFactory]
    A --> D[StockReportAnalyzer]
    B --> E[Yahoo Finance API]
    B --> F[OpenRouter API]
    C --> G[Badge3DModel]
    G --> H[DiscBadge/RectangularBadge/TriangularBadge]
    A --> I[ComplexityAnalyzer]
    A --> J[Genetic Algorithm]
    D --> K[SentimentAnalyzer]
    K --> L[NRC VAD Lexicon]
```

## Main Program Flow

```mermaid
flowchart TD
    Start([Start]) --> Init[Initialize CrazyStockBadge]
    Init --> ParseArgs[Parse Command Line Arguments]
    ParseArgs --> GetTicker[Get Ticker Symbol]
    GetTicker --> FetchData[Fetch Stock Data]
    FetchData --> AnalyzeData[Perform Technical Analysis]
    AnalyzeData --> GenReport{Generate Report?}
    GenReport -- Yes --> CreateReport[Generate Stock Report]
    GenReport -- No --> SkipReport[Skip Report]
    CreateReport --> AnalyzeSentiment[Analyze Sentiment]
    SkipReport --> StartBadge[Start Badge Generation]
    AnalyzeSentiment --> StartBadge
    StartBadge --> InitGA[Initialize Genetic Algorithm]
    InitGA --> RunGA[Run Genetic Algorithm]
    RunGA --> GenerateBadge[Generate Best Badge]
    GenerateBadge --> SaveSCAD[Save SCAD File]
    SaveSCAD --> End([End])
```

## Genetic Algorithm Flow

```mermaid
flowchart TD
    StartGA([Start GA]) --> InitPop[Initialize Population]
    InitPop --> Evaluate[Evaluate Fitness]
    Evaluate --> Generation[Process Generation]
    Generation --> Select[Select Parents]
    Select --> Crossover[Crossover]
    Crossover --> Mutate[Mutation]
    Mutate --> NewPop[Create New Population]
    NewPop --> CheckGen{Max Generations?}
    CheckGen -- No --> Evaluate
    CheckGen -- Yes --> BestSol[Get Best Solution]
    BestSol --> EndGA([End GA])
```

## Badge Generation Process

```mermaid
flowchart TD
    StartBadge([Start Badge Generation]) --> ConvertGenes[Convert Genes to Badge Parameters]
    ConvertGenes --> CreateBadge[Create Badge Object]
    CreateBadge --> GenBase[Generate Base]
    GenBase --> GenTerrain[Generate Terrain]
    GenTerrain --> GenText[Generate Text]
    GenText --> CombineModels[Combine Models]
    CombineModels --> AnalyzeComplexity[Analyze Complexity]
    AnalyzeComplexity --> CalcFitness[Calculate Fitness]
    CalcFitness --> EndBadge([End Badge Generation])
```

## Sentiment Analysis Flow

```mermaid
flowchart TD
    StartSA([Start Sentiment Analysis]) --> LoadLexicon[Load NRC VAD Lexicon]
    LoadLexicon --> ReadReport[Read Stock Report]
    ReadReport --> Preprocess[Preprocess Text]
    Preprocess --> AnalyzeText[Analyze Text]
    AnalyzeText --> CalcVAD[Calculate VAD Scores]
    CalcVAD --> AnalyzeFinancial[Analyze Financial Terms]
    AnalyzeFinancial --> GenSummary[Generate Emotional Summary]
    GenSummary --> SaveAnalysis[Save Analysis]
    SaveAnalysis --> EndSA([End Sentiment Analysis])
```

## Data Flow

```mermaid
flowchart LR
    YahooFinance[Yahoo Finance API] --> StockData[Stock Data]
    StockData --> TechnicalAnalysis[Technical Analysis]
    TechnicalAnalysis --> MarketReport[Market Report]
    MarketReport --> SentimentAnalysis[Sentiment Analysis]
    SentimentAnalysis --> BadgeParameters[Badge Parameters]
    BadgeParameters --> GeneticAlgorithm[Genetic Algorithm]
    GeneticAlgorithm --> BadgeModel[Badge Model]
    BadgeModel --> ComplexityAnalysis[Complexity Analysis]
    ComplexityAnalysis --> FitnessScore[Fitness Score]
    FitnessScore --> GeneticAlgorithm
    GeneticAlgorithm --> FinalBadge[Final Badge]
    FinalBadge --> SCADFile[SCAD File]
```

## Key Components and Their Relationships

1. **CrazyStockBadge (Main CLI)**: The central controller that orchestrates the entire process.
2. **MarketDataManager**: Fetches stock data and performs technical analysis.
3. **StockReportAnalyzer**: Analyzes sentiment in stock reports.
4. **BadgeFactory**: Creates different types of 3D badge models.
5. **Badge3DModel**: Base class for all badge types with common functionality.
6. **ComplexityAnalyzer**: Analyzes the complexity of 3D models for fitness evaluation.
7. **Genetic Algorithm**: Optimizes badge design for maximum "craziness" and complexity.

The program follows these main steps:
1. Fetch stock data for a given ticker symbol
2. Perform technical analysis on the data
3. Generate a market report using OpenRouter API
4. Analyze sentiment in the report
5. Use a genetic algorithm to generate a 3D badge design
6. Evaluate badge designs based on complexity metrics
7. Save the final badge as a SCAD file for 3D printing

This logical flow diagram provides a clear understanding of how the different components of the Crazy Stock Badges project interact and the overall program flow.
