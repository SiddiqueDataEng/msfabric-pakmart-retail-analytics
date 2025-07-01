-- ============================================================
-- PakMart Traders – Drop and Create Tables
-- SQL Analytics Endpoint schema for the Silver lakehouse
-- Pakistani Retail context (currency: PKR)
-- ============================================================

DROP PROCEDURE IF EXISTS dbo.DropAndCreatePakMartTables
GO

CREATE PROCEDURE dbo.DropAndCreatePakMartTables
    @Schema varchar(10)
AS
BEGIN
    DECLARE @SQL varchar(8000)

    IF NOT EXISTS (SELECT * FROM sys.schemas WHERE name = 'stage')
        EXEC ('CREATE SCHEMA [stage]')

    SET @SQL = '
    -- ─── Dimension: City (Pakistani cities, provinces, territories) ───────────
    DROP TABLE IF EXISTS [' + @Schema + '].[DimCity];
    CREATE TABLE [' + @Schema + '].[DimCity] (
        [CityKey]                  INT           NOT NULL,
        [WWICityID]                INT           NOT NULL,
        [City]                     VARCHAR(100)  NOT NULL,
        [StateProvince]            VARCHAR(60)   NOT NULL,  -- e.g. Punjab, Sindh, KPK
        [Country]                  VARCHAR(60)   NOT NULL,  -- Pakistan
        [Continent]                VARCHAR(30)   NOT NULL,  -- Asia
        [SalesTerritory]           VARCHAR(60)   NOT NULL,  -- e.g. Karachi Region
        [Region]                   VARCHAR(30)   NOT NULL,
        [Subregion]                VARCHAR(30)   NOT NULL,
        [Location]                 VARCHAR(60)   NULL,      -- lat/lon string
        [LatestRecordedPopulation] BIGINT        NOT NULL,
        [ValidFrom]                DATETIME2(6)  NOT NULL,
        [ValidTo]                  DATETIME2(6)  NOT NULL,
        [LineageKey]               INT           NOT NULL
    );

    -- ─── Dimension: Customer (Pakistani businesses/individuals) ──────────────
    DROP TABLE IF EXISTS [' + @Schema + '].[DimCustomer];
    CREATE TABLE [' + @Schema + '].[DimCustomer] (
        [CustomerKey]     INT           NOT NULL,
        [WWICustomerID]   INT           NOT NULL,
        [Customer]        VARCHAR(150)  NOT NULL,
        [BillToCustomer]  VARCHAR(150)  NOT NULL,
        [Category]        VARCHAR(60)   NOT NULL,  -- Retailer/Wholesaler/Corporate/Government/Online
        [BuyingGroup]     VARCHAR(60)   NOT NULL,  -- PakMart Partners / Independent / ...
        [PrimaryContact]  VARCHAR(100)  NOT NULL,
        [PostalCode]      VARCHAR(10)   NULL,
        [ValidFrom]       DATETIME2(6)  NOT NULL,
        [ValidTo]         DATETIME2(6)  NOT NULL,
        [LineageKey]      INT           NOT NULL
    );

    -- ─── Dimension: Date (Pakistani fiscal year July–June) ───────────────────
    DROP TABLE IF EXISTS [' + @Schema + '].[DimDate];
    CREATE TABLE [' + @Schema + '].[DimDate] (
        [Date]                DATE         NOT NULL,
        [DayNumber]           INT          NOT NULL,
        [Day]                 VARCHAR(10)  NOT NULL,
        [Month]               VARCHAR(10)  NOT NULL,
        [ShortMonth]          VARCHAR(3)   NOT NULL,
        [CalendarMonthNumber] INT          NOT NULL,
        [CalendarMonthLabel]  VARCHAR(20)  NOT NULL,
        [CalendarYear]        INT          NOT NULL,
        [CalendarYearLabel]   VARCHAR(10)  NOT NULL,
        [FiscalMonthNumber]   INT          NOT NULL,  -- 1=July, 12=June
        [FiscalMonthLabel]    VARCHAR(20)  NOT NULL,
        [FiscalYear]          INT          NOT NULL,  -- e.g. 2020 = Jul-2019 to Jun-2020
        [FiscalYearLabel]     VARCHAR(10)  NOT NULL,
        [ISOWeekNumber]       INT          NOT NULL
    );

    -- ─── Dimension: Employee (Pakistani names, salesperson flag) ─────────────
    DROP TABLE IF EXISTS [' + @Schema + '].[DimEmployee];
    CREATE TABLE [' + @Schema + '].[DimEmployee] (
        [EmployeeKey]   INT           NOT NULL,
        [WWIEmployeeID] INT           NOT NULL,
        [Employee]      VARCHAR(100)  NOT NULL,
        [PreferredName] VARCHAR(50)   NOT NULL,
        [IsSalesperson] BIT           NOT NULL,
        [Photo]         VARCHAR(200)  NULL,
        [ValidFrom]     DATETIME2(6)  NOT NULL,
        [ValidTo]       DATETIME2(6)  NOT NULL,
        [LineageKey]    INT           NOT NULL
    );

    -- ─── Dimension: Stock Item (Food, Clothing, Electronics, Household, Beverage) ─
    DROP TABLE IF EXISTS [' + @Schema + '].[DimStockItem];
    CREATE TABLE [' + @Schema + '].[DimStockItem] (
        [StockItemKey]           INT             NOT NULL,
        [WWIStockItemID]         INT             NOT NULL,
        [StockItem]              VARCHAR(200)    NOT NULL,
        [Color]                  VARCHAR(30)     NOT NULL,
        [SellingPackage]         VARCHAR(50)     NOT NULL,
        [BuyingPackage]          VARCHAR(50)     NOT NULL,
        [Brand]                  VARCHAR(100)    NOT NULL,
        [Size]                   VARCHAR(50)     NOT NULL,
        [LeadTimeDays]           INT             NOT NULL,
        [QuantityPerOuter]       INT             NOT NULL,
        [IsChillerStock]         BIT             NOT NULL,
        [Barcode]                VARCHAR(20)     NULL,
        [TaxRate]                DECIMAL(18,3)   NOT NULL,  -- Pakistani GST 17%
        [UnitPrice]              DECIMAL(18,2)   NOT NULL,  -- PKR
        [RecommendedRetailPrice] DECIMAL(18,2)   NULL,      -- PKR
        [TypicalWeightPerUnit]   DECIMAL(18,3)   NULL,      -- kg
        [Photo]                  VARCHAR(200)    NULL,
        [ValidFrom]              DATETIME2(6)    NOT NULL,
        [ValidTo]                DATETIME2(6)    NOT NULL,
        [LineageKey]             INT             NOT NULL
    );

    -- ─── Fact: Sale (all monetary values in PKR) ──────────────────────────────
    DROP TABLE IF EXISTS [' + @Schema + '].[FactSale];
    CREATE TABLE [' + @Schema + '].[FactSale] (
        [SaleKey]           BIGINT          NOT NULL,
        [CityKey]           INT             NOT NULL,  -- FK → DimCity
        [CustomerKey]       INT             NOT NULL,  -- FK → DimCustomer
        [BillToCustomerKey] INT             NOT NULL,  -- FK → DimCustomer
        [StockItemKey]      INT             NOT NULL,  -- FK → DimStockItem
        [InvoiceDateKey]    DATE            NOT NULL,  -- FK → DimDate
        [DeliveryDateKey]   DATE            NULL,
        [SalespersonKey]    INT             NOT NULL,  -- FK → DimEmployee
        [WWIInvoiceID]      INT             NOT NULL,
        [Description]       VARCHAR(8000)   NOT NULL,
        [Package]           VARCHAR(50)     NOT NULL,
        [Quantity]          INT             NOT NULL,
        [UnitPrice]         DECIMAL(18,2)   NOT NULL,  -- PKR
        [TaxRate]           DECIMAL(18,3)   NOT NULL,  -- 17.000 = 17% GST
        [TotalExcludingTax] DECIMAL(18,2)   NOT NULL,  -- PKR
        [TaxAmount]         DECIMAL(18,2)   NOT NULL,  -- PKR
        [Profit]            DECIMAL(18,2)   NOT NULL,  -- PKR
        [TotalIncludingTax] DECIMAL(18,2)   NOT NULL,  -- PKR
        [TotalDryItems]     INT             NOT NULL,
        [TotalChillerItems] INT             NOT NULL,
        [LineageKey]        INT             NOT NULL
    );'

    EXEC (@SQL)
END
GO

-- Create tables in both stage and dbo schemas
EXEC dbo.DropAndCreatePakMartTables @Schema = 'stage'
EXEC dbo.DropAndCreatePakMartTables @Schema = 'dbo'
GO
