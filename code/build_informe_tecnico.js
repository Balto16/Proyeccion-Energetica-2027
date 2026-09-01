const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, ImageRun, PageBreak,
  Header, Footer, PageNumber, LevelFormat, convertInchesToTwip, TabStopType, TabStopPosition,
  HorizontalPositionAlign, VerticalPositionAlign, HorizontalPositionRelativeFrom, VerticalPositionRelativeFrom, TextWrappingType, TextWrappingSide,
} = require("docx");

const TEAL = "4D8270";
const SAGE = "6DA894";
const PURPLE = "4C2E6A";
const GOLD = "B8860B";
const DARKGREEN = "244E38";
const LIGHTGRAY = "F2F2F2";
const LIGHTGREEN_TINT = "EEF3F0";
const LIGHTGOLD_TINT = "FBF6EA";
const GRAY = "5c6163";

function h1(text, num) {
  // Banner de sección sólido (spec 2I del sistema de diseño): franja de ancho
  // completo en verde TEAL con el número y el título en blanco.
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    borders: { top:{style:BorderStyle.NONE}, bottom:{style:BorderStyle.NONE}, left:{style:BorderStyle.NONE}, right:{style:BorderStyle.NONE}, insideHorizontal:{style:BorderStyle.NONE}, insideVertical:{style:BorderStyle.NONE} },
    rows: [ new TableRow({ children: [ new TableCell({
      width: { size: 9360, type: WidthType.DXA },
      shading: { type: ShadingType.CLEAR, fill: TEAL },
      margins: { top: 160, bottom: 160, left: 220, right: 220 },
      children: [ new Paragraph({
        spacing: { before: 0, after: 0 },
        children: [
          ...(num ? [new TextRun({ text: num + "  ", bold: true, color: "CFE3D8", size: 26 })] : []),
          new TextRun({ text, bold: true, color: "FFFFFF", size: 26 }),
        ],
      }) ],
    }) ] }) ],
  });
}
function h1Spacer() {
  return new Paragraph({ spacing: { before: 260, after: 160 } });
}
function h2(text) {
  return new Paragraph({ text, heading: HeadingLevel.HEADING_2, spacing: { before: 260, after: 120 } });
}
function calloutBox(title, text) {
  // Nota destacada (spec 2K): borde izquierdo grueso en dorado, fondo tenue.
  return new Table({
    width: { size: 9360, type: WidthType.DXA },
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: "E8DCC0" },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "E8DCC0" },
      right: { style: BorderStyle.SINGLE, size: 4, color: "E8DCC0" },
      left: { style: BorderStyle.SINGLE, size: 36, color: GOLD },
      insideHorizontal: { style: BorderStyle.NONE }, insideVertical: { style: BorderStyle.NONE },
    },
    rows: [ new TableRow({ cantSplit: true, children: [ new TableCell({
      margins: { top: 160, bottom: 160, left: 220, right: 220 },
      children: [
        new Paragraph({ spacing: { after: 60 }, children: [new TextRun({ text: title, bold: true, size: 18, color: "8A6A14" })] }),
        new Paragraph({ spacing: { after: 0 }, children: [new TextRun({ text, size: 20 })] }),
      ],
    }) ] }) ],
  });
}
function p(text, opts = {}) {
  return new Paragraph({
    spacing: { after: 140, line: 276 },
    children: [new TextRun({ text, ...opts })],
  });
}
function pRuns(runs, opts = {}) {
  return new Paragraph({ spacing: { after: 140, line: 276 }, ...opts, children: runs });
}
function bullet(text, level = 0) {
  return new Paragraph({
    text, bullet: { level }, spacing: { after: 80 },
  });
}

function cell(text, { bold = false, shade = null, width = null, align = AlignmentType.LEFT, color = null, size = 19 } = {}) {
  return new TableCell({
    width: width ? { size: width, type: WidthType.DXA } : undefined,
    shading: shade ? { type: ShadingType.CLEAR, fill: shade } : undefined,
    margins: { top: 60, bottom: 60, left: 100, right: 100 },
    children: [new Paragraph({
      alignment: align,
      children: [new TextRun({ text, bold, color: color || undefined, size })],
    })],
  });
}

function dataTable(headers, rows, colWidths) {
  const tableWidth = colWidths.reduce((a, b) => a + b, 0);
  const headerRow = new TableRow({
    tableHeader: true,
    children: headers.map((hdr, i) => cell(hdr, { bold: true, shade: TEAL, width: colWidths[i], align: AlignmentType.CENTER, color: "FFFFFF", size: 18 })),
  });
  const bodyRows = rows.map((r, ridx) => new TableRow({
    children: r.map((val, i) => cell(val, { width: colWidths[i], align: i === 0 ? AlignmentType.LEFT : AlignmentType.CENTER, shade: ridx % 2 === 1 ? LIGHTGRAY : null })),
  }));
  return new Table({
    width: { size: tableWidth, type: WidthType.DXA },
    columnWidths: colWidths,
    rows: [headerRow, ...bodyRows],
    borders: {
      top: { style: BorderStyle.SINGLE, size: 4, color: "AAAAAA" },
      bottom: { style: BorderStyle.SINGLE, size: 4, color: "AAAAAA" },
      left: { style: BorderStyle.SINGLE, size: 4, color: "AAAAAA" },
      right: { style: BorderStyle.SINGLE, size: 4, color: "AAAAAA" },
      insideHorizontal: { style: BorderStyle.SINGLE, size: 4, color: "DDDDDD" },
      insideVertical: { style: BorderStyle.SINGLE, size: 4, color: "DDDDDD" },
    },
  });
}

function imagePar(path, width, height, caption) {
  const data = fs.readFileSync(path);
  return [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 60 },
      children: [new ImageRun({ data, transformation: { width, height }, type: "png" })],
    }),
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 220 },
      children: [new TextRun({ text: caption, italics: true, size: 18, color: GRAY })],
    }),
  ];
}

const doc = new Document({
  styles: {
    default: {
      document: { run: { font: "Calibri", size: 22 } },
    },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { bold: true, size: 28, color: TEAL, font: "Calibri" },
        paragraph: { spacing: { before: 320, after: 160 } } },
      { id: "Heading2", name: "Heading 2", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { bold: true, size: 24, color: PURPLE, font: "Calibri" },
        paragraph: { spacing: { before: 260, after: 120 } } },
    ],
  },
  numbering: {
    config: [
      { reference: "refs-num", levels: [{ level: 0, format: LevelFormat.DECIMAL, text: "[%1]", alignment: AlignmentType.LEFT, style: { paragraph: { indent: { left: 420, hanging: 360 } } } }] },
    ],
  },
  sections: [
    // ---------------- PORTADA ----------------
    {
      properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } } },
      children: [
        new Paragraph({
          children: [ new ImageRun({
            data: fs.readFileSync("../figures/portada_diagonal.png"),
            transformation: { width: 850, height: 1100 },
            type: "png",
            floating: {
              horizontalPosition: { relative: HorizontalPositionRelativeFrom.PAGE, align: HorizontalPositionAlign.LEFT },
              verticalPosition: { relative: VerticalPositionRelativeFrom.PAGE, align: VerticalPositionAlign.TOP },
              wrap: { type: TextWrappingType.NONE },
              behindDocument: true,
              allowOverlap: true,
            },
          }) ],
        }),
        new Paragraph({ spacing: { before: 700 }, alignment: AlignmentType.LEFT,
          children: [new TextRun({ text: "DINAGEA · UTP", bold: true, size: 22, color: "FFFFFF" })] }),
        new Paragraph({ spacing: { before: 80 }, alignment: AlignmentType.LEFT,
          children: [new TextRun({ text: "PROYECCIÓN ENERGÉTICA", bold: true, size: 46, color: "FFFFFF" })] }),
        new Paragraph({ spacing: { before: 40, after: 900 }, alignment: AlignmentType.LEFT,
          children: [new TextRun({ text: "CONSUMO, DEMANDA, TARIFA Y COSTO · 2026–2027", bold: true, size: 24, color: "E8F0EC" })] }),

        new Paragraph({ spacing: { before: 4200 }, alignment: AlignmentType.LEFT,
          children: [new TextRun({ text: "Análisis comparativo mediante dos metodologías cuantitativas independientes, validadas con el pliego tarifario oficial de ASEP", italics: true, size: 22, color: GRAY })] }),
        new Paragraph({ spacing: { before: 900 }, alignment: AlignmentType.LEFT,
          children: [new TextRun({ text: "Informe técnico", size: 22, color: DARKGREEN, bold: true })] }),
        new Paragraph({ alignment: AlignmentType.LEFT,
          children: [new TextRun({ text: `Panamá, ${new Date().toLocaleDateString('es-PA', { year: 'numeric', month: 'long', day: 'numeric' })}`, size: 22 })] }),
        new Paragraph({ spacing: { before: 1600 }, alignment: AlignmentType.LEFT,
          children: [new TextRun({ text: "Fuente de datos: registros de facturación eléctrica por medidor, todas las sedes, enero 2022 – mayo 2026", size: 18, color: GRAY })] }),
      ],
    },
    // ---------------- CUERPO ----------------
    {
      properties: {
        page: { size: { width: 12240, height: 15840 }, margin: { top: 1440, bottom: 1440, left: 1440, right: 1440 } },
      },
      headers: {
        default: new Header({ children: [new Paragraph({ alignment: AlignmentType.RIGHT,
          children: [new TextRun({ text: "UTP – Proyección energética 2026–2027", size: 16, color: GRAY })] })] }),
      },
      footers: {
        default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
          children: [new TextRun({ children: [PageNumber.CURRENT], size: 18, color: GRAY })] })] }),
      },
      children: [
        h1("Introducción y objetivo", "1."),
        h1Spacer(),
        p("Este informe presenta la proyección del consumo de energía eléctrica, la demanda facturada, la tarifa efectiva y el costo total de energía de la Universidad Tecnológica de Panamá (todas las sedes) para los años 2026 y 2027, a partir del histórico de facturación por medidor correspondiente al período enero de 2022 a mayo de 2026."),
        p("El objetivo es contar con una base cuantitativa para la planificación presupuestaria y energética institucional. Para dar robustez a la proyección se aplican dos métodos independientes, ampliamente documentados en la literatura de forecasting de demanda energética, y se contrastan sus resultados: si ambos convergen a cifras del mismo orden de magnitud, la proyección se considera consistente; si divergen, la diferencia se reporta como el rango de incertidumbre del pronóstico."),

        h1("Datos utilizados", "2."),
        h1Spacer(),
        p("La base de datos contiene 2,798 registros de facturación mensual por medidor (entre 52 y 54 medidores activos según el mes), con las variables: fecha (año/mes), importe facturado ($), demanda (kW) y consumo (kWh). Los registros provienen de la factura eléctrica de las tres empresas distribuidoras que dan servicio a las sedes de la UTP: Elektra Noreste, S.A. (ENSA), Empresa de Distribución Eléctrica Metro-Oeste, S.A. (EDEMET) y Empresa de Distribución Eléctrica Chiriquí, S.A. (EDECHI). Los registros se agregaron a nivel mensual institucional (suma de todos los medidores) para construir una serie de tiempo de 53 observaciones (enero 2022 a mayo 2026). El dataset consolidado, junto con el código de limpieza y agregación, se adjunta en el repositorio del proyecto (ver Anexo A)."),
        bullet("Consumo mensual (kWh): suma de la energía activa facturada de todos los medidores."),
        bullet("Demanda mensual (kW): suma de la demanda facturada de todos los medidores (aproximación agregada de la demanda del sistema; no equivale a una medición coincidente simultánea, pero es consistente para efectos de tendencia)."),
        bullet("Importe ($) y tarifa efectiva ($/kWh = importe / consumo): refleja la tarifa promedio ponderada realmente pagada, incluyendo cargos por energía, demanda y otros recargos regulados."),
        p("Para el análisis se usaron todos los meses cuyos registros estuvieron completos, cargados y revisados en la base de datos al momento de este informe. No se identificaron valores de consumo o demanda negativos; se registraron 5 ajustes menores de importe con signo negativo (créditos/notas de crédito), que no afectan materialmente los totales agregados."),

        h1("Metodología", "3."),
        h1Spacer(),
        p("Se seleccionaron dos métodos de naturaleza distinta y complementaria: uno explicativo/econométrico y otro puramente basado en la dinámica temporal de la serie. Esta combinación es la práctica recomendada en estudios de proyección de demanda eléctrica, ya que permite verificar que la tendencia estimada no depende de un solo marco de modelado."),

        h2("3.1 Método 1: Regresión Lineal Múltiple (MLR) con tendencia y estacionalidad"),
        p("Se ajustó, para cada variable (consumo, demanda, tarifa), un modelo de la forma:"),
        pRuns([new TextRun({ text: "Yₜ = β₀ + β₁·t + Σ βₘ·Dₘ,ₜ + εₜ", italics: true, size: 22 })], { alignment: AlignmentType.CENTER }),
        p("donde t es el índice temporal (tendencia lineal de largo plazo) y Dₘ son variables dummy para 11 de los 12 meses del año (enero como categoría base), que capturan la estacionalidad académica y climática (períodos de receso, temporada seca/lluviosa). Los coeficientes se estimaron por mínimos cuadrados ordinarios (OLS)."),
        p("Este enfoque replica la metodología estándar de modelos de demanda energética sectorial de la U.S. Energy Information Administration (EIA) y de estudios académicos de referencia como Kialashaki & Reisel (2013), quienes desarrollaron modelos de regresión múltiple para proyectar la demanda energética residencial de EE.UU. hasta 2030, validándolos contra redes neuronales artificiales con resultados convergentes.", ),

        h2("3.2 Método 2: SARIMA estacional (modelo Airline de Box-Jenkins)"),
        p("El segundo método aplica un modelo SARIMA(0,1,1)(0,1,1)₁₂ sobre el logaritmo natural de cada serie. Esta especificación, conocida como “modelo Airline”, fue identificada originalmente por Box & Jenkins (1976) para series mensuales con tendencia y estacionalidad multiplicativa (la amplitud del ciclo estacional crece proporcionalmente al nivel de la serie, patrón que se observa también en el consumo institucional). El modelo se define, sobre wₜ = (1−B)(1−B¹²) ln(Yₜ), como:"),
        pRuns([new TextRun({ text: "wₜ = eₜ − θ·eₜ₋₁ − Θ·eₜ₋₁₂ + θΘ·eₜ₋₁₃", italics: true, size: 22 })], { alignment: AlignmentType.CENTER }),
        p("donde B es el operador de rezago, y θ, Θ son los parámetros de media móvil regular y estacional, estimados por suma condicional de cuadrados (CSS) mediante optimización numérica. A diferencia de un modelo de suavizado exponencial (Holt-Winters), que debe actualizar recursivamente ~15 estados (nivel, tendencia y 12 índices estacionales), el modelo Airline solo estima 2 parámetros libres, lo que lo hace considerablemente más estable en series cortas como la de este estudio (53 observaciones, 4.4 ciclos estacionales completos). Se evaluó explícitamente un ajuste preliminar con Holt-Winters y se descartó por sobreajuste: ver nota metodológica en la sección 3.3."),

        h2("3.3 Validación de los métodos con datos reales (backtesting)"),
        p("Antes de usar los métodos para proyectar 2026-2027, se puso a prueba qué tan bien funcionan con datos que ya se conocen. Se entrenó cada método usando solo la información de 2022 a 2024, se le pidió predecir los 12 meses de 2025, y se comparó esa predicción contra lo que realmente ocurrió. El error se mide con el MAPE (error porcentual promedio): entre más bajo, mejor. También se incluye el resultado de Holt-Winters, un tercer método que se descartó por su bajo desempeño:"),
        dataTable(
          ["Variable", "MAPE Método 1 (MLR)", "MAPE Método 2 (SARIMA Airline)", "MAPE Holt-Winters (descartado)"],
          [
            ["Consumo (kWh)", "11.8 %", "7.8 %", "22.9 %"],
            ["Demanda (kW)", "12.2 %", "5.2 %", "5.4 %"],
            ["Tarifa ($/kWh)", "6.2 %", "4.5 %", "4.7 %"],
          ],
          [2600, 2300, 2600, 2300]
        ),
        p("El SARIMA Airline tuvo mejor desempeño que el MLR en las tres variables, y evitó el problema del Holt-Winters. Con solo 53 meses de datos, un método como Holt-Winters necesita calcular muchos valores internos a la vez (el nivel general, la tendencia, y un ajuste distinto para cada uno de los 12 meses del año), y con tan poca historia esos cálculos se vuelven poco confiables: en las pruebas, llegó a predecir la tarifa peor de lo que se obtendría usando simplemente el promedio histórico. Por eso se descartó, y se usó en su lugar el SARIMA Airline, que solo necesita calcular 2 valores internos y dio mejores resultados en las tres variables."),

        h2("3.4 Comparación con la tarifa oficial de ASEP"),
        p("Los métodos 1 y 2 tratan la tarifa como una serie extrapolable estadísticamente, sin usar información regulatoria real. Para reducir esa debilidad se incorporó el histórico oficial de cargos de ASEP (2023 al primer semestre de 2026) para las distribuidoras EDEMET, ENSA y EDECHI, con el detalle de cargo fijo, cargo de energía ($/kWh) y cargo de demanda ($/kW) por tarifa y período de vigencia. El pliego tarifario completo se adjunta en el repositorio del proyecto (ver Anexo A)."),
        calloutBox("Hallazgo · Choque regulatorio documentado", "Entre el 23 de octubre de 2024 y junio de 2025, un fallo de la Corte Suprema de Justicia (Resolución AN No. 19632-Elec) revirtió la tarifa MTD de ENSA a un pliego provisional de 2018. La posterior Resolución AN No. 19850-Elec (2.º semestre 2025) la incrementó +32% en cargo de energía y +40% en cargo de demanda. Esto explica, con evidencia documentada, por qué la tarifa no sigue una tendencia estadística suave."),
        new Paragraph({ spacing: { after: 140 } }),
        p("Este hallazgo permitió identificar la causa estructural de la baja explicación del ajuste de tendencia en la tarifa (sección 4.3). No se trata de ruido estadístico: es un choque regulatorio documentado, que ningún modelo de tendencia o de suavizado puede anticipar sin esta información exógena."),
        p("A partir del listado oficial de los 65 medidores de la UTP (sede, distribuidora, tarifa asignada) se construyó un motor de cálculo exacto: para cada medidor y cada mes se identifica su distribuidora (ENSA, EDEMET o EDECHI), su clase tarifaria (BTS, BTD o MTD) y, en el caso de BTD, el escalón de consumo que le corresponde ese mes (0-10k, 10k-30k, 30k-50k o >50k kWh, según define el pliego), y se le aplica el cargo de energía, cargo de demanda y cargo fijo exactos de ese período. Esto reemplaza el supuesto usado en una versión anterior de este informe, que aplicaba una sola tarifa (MTD de ENSA) a toda la institución."),
        p("El cruce con el listado de medidores reveló un hallazgo relevante: la tarifa MTD no pertenece únicamente al Campus Metropolitano (Sede Principal). También la Extensión de Tocumen (ENSA) y el Centro Regional de Azuero (EDEMET) facturan bajo MTD. En conjunto, los 4 medidores MTD de la UTP —repartidos en 3 sedes— concentran 75.3% del consumo institucional, cifra consistente con el rango de 70-80% estimado inicialmente, pero con una composición geográfica distinta a la asumida."),
        p("Con el motor de cálculo exacto, el importe teórico mensual (sumado por medidor) se comparó contra el importe real facturado. El ajuste mejoró sustancialmente frente a la aproximación anterior: en el período de enero 2023 a junio de 2025, el error medio (MAPE) bajó de 10.1% a 3.7%. Sin embargo, a partir de julio de 2025 —el mismo punto donde entra en vigor la Resolución AN No. 19850-Elec— aparece una sobreestimación sistemática que empieza en 22.9% y desciende de forma gradual y consistente mes a mes hasta 12.9% en mayo de 2026."),
        calloutBox("Nota metodológica · Posible tratamiento tarifario especial", "Que el motor exacto por medidor reduzca el error a 3.7% antes de julio de 2025 y aun así sobreestime de forma sistemática después, con una tendencia que se achica mes a mes, sugiere que la UTP recibe algún tratamiento tarifario institucional o gubernamental (descuentos, exoneraciones o fondos como el FET/FTO) que se intensificó con el alza de la Resolución AN No. 19850-Elec y que podría estarse normalizando gradualmente. Esta información no está disponible en los datos suministrados; se recomienda confirmarla con la administración (ver sección 6)."),
        new Paragraph({ spacing: { after: 140 } }),
        p("Para proyectar el costo 2026-2027, se calculó una tarifa institucional ponderada por el consumo y la demanda reales de cada medidor en el régimen vigente (julio 2025 a mayo 2026): cargo de energía $0.18778/kWh y cargo de demanda $18.97/kW (más representativos que usar la tarifa MTD sola, ya que incorporan el peso real de cada sede). Sobre esa tarifa ponderada se aplicó el mismo tipo de factor de calibración usado antes, ahora recalculado con el motor exacto:"),
        pRuns([new TextRun({ text: "factor = Importe real facturado ÷ Importe teórico (motor exacto por medidor)", italics: true, size: 22 })], { alignment: AlignmentType.CENTER }),
        p("El resultado es factor = 0.842 (11 meses, desviación estándar 0.025, coeficiente de variación 3.0%), prácticamente igual al 0.836 obtenido con la aproximación anterior. Esto es una buena noticia metodológica: aunque el motor de cálculo es ahora mucho más preciso y detallado, la magnitud del ajuste necesario no cambió, lo que refuerza que la brecha no se debe a un error de qué tarifa se estaba usando, sino a un factor externo (posible tratamiento especial) no documentado en el pliego comercial."),
        p("Para proyectar 2026-2027, este factor se aplica sobre la tarifa ponderada, usando el consumo y la demanda que ya proyectaron los métodos 1 y 2:"),
        pRuns([new TextRun({ text: "Costo proyectado = factor × (Consumo × $0.18778 + Demanda × $18.97 + Cargo Fijo total mensual)", italics: true, size: 22 })], { alignment: AlignmentType.CENTER }),
        p("El resultado (Método 3) se reporta en la sección 4.4 junto a los métodos 1 y 2. El código completo de este motor de cálculo, el listado de medidores y el detalle mes a mes están disponibles en el repositorio del proyecto (Anexo A)."),

        h2("3.5 Consumo por sede"),
        p("El listado de medidores permite, por primera vez en este informe, desagregar el consumo histórico por sede. El Campus Víctor Levi Sasso (Sede Principal, Panamá) concentra 70.5% del consumo institucional acumulado 2022-mayo 2026, seguido por la Extensión de Tocumen (6.2%) y el Centro Regional de Chiriquí (5.4%). Las demás 8 sedes se reparten el 17.9% restante."),
        ...imagePar("../figures/fig_consumo_por_sede.png", 540, 290, "Figura 1. Consumo eléctrico acumulado por sede, 2022 a mayo de 2026."),
        p("Esta desagregación por sede es descriptiva: las proyecciones de los métodos 1, 2 y 3 (secciones 4.1 a 4.4) se calculan sobre el consumo institucional agregado, no sede por sede. Generar una proyección independiente para cada una de las 11 sedes es posible con los datos ahora disponibles, pero implica repetir el proceso de modelado (MLR y SARIMA) 11 veces y queda fuera del alcance de esta versión del informe; se puede desarrollar como una fase siguiente si es de interés."),

        new Paragraph({ children: [new PageBreak()] }),

        h1("Resultados: histórico y proyección 2026–2027", "4."),
        h1Spacer(),

        h2("4.1 Consumo de energía"),
        ...imagePar("../figures/fig_consumo.png", 570, 273, "Figura 2. Consumo eléctrico mensual histórico (2022–may. 2026) y proyectado (jun. 2026–2027) según ambos métodos."),
        dataTable(
          ["Año", "Consumo (MWh)", "Método"],
          [
            ["2022 (real)", "11,997", "—"],
            ["2023 (real)", "13,880", "—"],
            ["2024 (real)", "15,264", "—"],
            ["2025 (real)", "15,385", "—"],
            ["2026 (ene–may real + jun–dic proyectado)", "16,038", "Método 1 – MLR"],
            ["2026 (ene–may real + jun–dic proyectado)", "15,824", "Método 2 – SARIMA"],
            ["2027 (proyección completa)", "17,389", "Método 1 – MLR"],
            ["2027 (proyección completa)", "17,488", "Método 2 – SARIMA"],
          ],
          [4200, 2400, 2700]
        ),
        p("Ambos métodos proyectan continuidad del crecimiento observado entre 2022 y 2025 (tasa compuesta anual real de 8.6%), con una diferencia entre métodos de apenas 1.3% para 2026 y 0.6% para 2027. El consumo 2027 se estima en un rango muy estrecho de 17,389–17,488 MWh (promedio ≈ 17,438 MWh)."),

        h2("4.2 Demanda facturada"),
        ...imagePar("../figures/fig_demanda.png", 570, 273, "Figura 3. Demanda facturada mensual agregada, histórica y proyectada."),
        dataTable(
          ["Año", "Demanda pico anual (kW)", "Método"],
          [
            ["2022 (real)", "4,490", "—"],
            ["2023 (real)", "4,983", "—"],
            ["2024 (real)", "5,102", "—"],
            ["2025 (real)", "4,940", "—"],
            ["2026", "5,084", "Método 1 – MLR"],
            ["2026", "5,084", "Método 2 – SARIMA"],
            ["2027", "5,174", "Método 1 – MLR"],
            ["2027", "5,276", "Método 2 – SARIMA"],
          ],
          [4200, 2400, 2700]
        ),
        p("La demanda pico se ha mantenido relativamente estable entre 4,900 y 5,100 kW en el período histórico. Ambos métodos coinciden en que 2026 se mantendrá en ese rango, y proyectan un incremento moderado hacia 5,200–5,300 kW en 2027 (diferencia entre métodos de solo 2.0%). Dado que la tarifa MTD/BTD no factura por capacidad contratada sino por demanda máxima registrada (el intervalo de 10-15 minutos de mayor potencia dentro del mes, multiplicado por el cargo de demanda), un solo pico puntual determina el cargo de todo ese mes; esto hace especialmente valioso el control operativo de picos simultáneos entre edificios, más que la gestión de una capacidad fija."),

        h2("4.3 Tarifa efectiva de energía"),
        ...imagePar("../figures/fig_tarifa.png", 570, 273, "Figura 4. Tarifa efectiva mensual (importe/consumo), histórica y proyectada."),
        p("La tarifa efectiva ($/kWh) ha oscilado entre $0.19 y $0.25/kWh en el histórico. Su variación no es ruido aleatorio: como se documenta en la sección 3.4, un fallo de la Corte Suprema de Justicia revirtió la tarifa a un pliego de 2018 entre octubre de 2024 y junio de 2025, seguido de un alza regulatoria de +32% en el cargo de energía en el segundo semestre de 2025. Por eso el ajuste de tendencia del Método 1 explica poco de su varianza (R² = 0.24): la tarifa depende de decisiones regulatorias documentadas, no de un patrón determinístico. El Método 2 (SARIMA) valida mejor en backtesting (MAPE 4.5% vs. 6.2% del MLR) al modelar la dependencia temporal directamente. Incorporando el pliego real calibrado (sección 3.4), la tarifa efectiva 2027 implícita es de $0.211/kWh, coincidente con el Método 1 y ligeramente por debajo del Método 2 ($0.221)."),

        h2("4.4 Costo total de energía"),
        ...imagePar("../figures/fig_costo_anual.png", 570, 300, "Figura 5. Costo anual de energía: real (2022–2025) vs. proyectado (2026–2027) por los tres métodos."),
        dataTable(
          ["Año", "Costo (US$)", "Tarifa prom. ($/kWh)", "Método"],
          [
            ["2022 (real)", "2,651,088", "0.2210", "—"],
            ["2023 (real)", "2,905,308", "0.2093", "—"],
            ["2024 (real)", "3,397,163", "0.2226", "—"],
            ["2025 (real)", "3,201,996", "0.2081", "—"],
            ["2026", "3,445,565", "0.2148", "Método 1 – MLR"],
            ["2026", "3,463,594", "0.2189", "Método 2 – SARIMA"],
            ["2026", "3,418,318", "0.2146", "Método 3 – Tarifa ASEP calibrada"],
            ["2027", "3,674,746", "0.2113", "Método 1 – MLR"],
            ["2027", "3,862,412", "0.2209", "Método 2 – SARIMA"],
            ["2027", "3,693,348", "0.2118", "Método 3 – Tarifa ASEP calibrada"],
          ],
          [2400, 2400, 2200, 2300]
        ),
        p("El Método 3, fundamentado en el pliego tarifario real de ASEP y no en extrapolación estadística, converge fuertemente con el Método 1 (diferencia de apenas 0.5% en 2027) y queda por debajo del Método 2. Esto sugiere que el SARIMA extrapola un componente de alza tarifaria algo mayor al que la estructura regulatoria vigente respalda hasta ahora."),

        h2("4.5 Desglose del costo: cargo por energía vs. cargo por demanda"),
        p("La tarifa MTD/BTD de ASEP no cobra por una capacidad contratada de antemano: mide la potencia en intervalos de 10-15 minutos a lo largo de todo el mes, identifica el intervalo de mayor valor, y ese único pico se multiplica por el cargo de demanda ($/kW). De forma independiente, el consumo acumulado del mes se multiplica por el cargo de energía ($/kWh). El importe total factura la suma de ambos componentes más el cargo fijo (este último, por debajo del 0.2% del total, es despreciable frente a los otros dos)."),
        ...imagePar("../figures/fig_desglose_energia_demanda.png", 560, 300, "Figura 6. Desglose del costo anual entre cargo por energía y cargo por demanda, 2023-2027."),
        p("El cargo por energía representa consistentemente 74-76% del costo total, y el cargo por demanda 24-26%, tanto en el histórico como en la proyección. Esta proporción se ha mantenido estable a pesar del choque regulatorio de 2024-2025 (sección 3.4), lo que indica que el alza tarifaria de la Resolución AN No. 19850-Elec afectó de forma similar a ambos cargos, sin desplazar la composición relativa del costo."),
        p("Esta estabilidad tiene una implicación práctica directa: dado que el cargo de demanda se determina por un único intervalo de 10-15 minutos al mes (no por una capacidad contratada ni por un promedio), la forma más efectiva de reducir ese ~24-25% del costo no es una negociación tarifaria, sino evitar que los picos de potencia de distintos edificios o sistemas (climatización, laboratorios, equipos de arranque pesado) coincidan en el mismo intervalo. Un solo evento de coincidencia de picos en un mes puede fijar el cargo de demanda de ese mes completo."),

        h1("Convergencia entre métodos", "5."),
        h1Spacer(),
        p("La diferencia relativa entre los tres métodos es pequeña: 2026 difiere menos de 1.3% en costo entre los tres; 2027 difiere 0.6% en consumo, 2.0% en demanda pico, y en costo el Método 1 y el Método 3 prácticamente coinciden ($3,674,746 vs. $3,693,348, diferencia de 0.5%), mientras el Método 2 queda 4.6% por encima de ambos. Esta convergencia era el criterio buscado al usar metodologías de naturaleza distinta (econométrica de tendencia, dependencia temporal, y estructura tarifaria regulatoria real, ahora calculada medidor por medidor), y confirma que la proyección no depende del marco de modelado elegido."),
        p("En términos prácticos, se recomienda presupuestar sobre el promedio de Método 1 y Método 3 (los dos más consistentes entre sí), usando el Método 2 como límite superior de sensibilidad:"),
        dataTable(
          ["Indicador 2027", "Método 1 (MLR)", "Método 2 (SARIMA)", "Método 3 (Tarifa ASEP)", "Recomendado"],
          [
            ["Consumo (MWh)", "17,389", "17,488", "—", "17,438"],
            ["Demanda pico (kW)", "5,174", "5,276", "—", "5,225"],
            ["Costo de energía (US$)", "3,674,746", "3,862,412", "3,693,348", "3,684,047"],
          ],
          [2600, 2000, 2000, 2000, 1700]
        ),

        h1("Conclusiones y recomendaciones", "6."),
        h1Spacer(),
        bullet("El consumo institucional muestra una tendencia de crecimiento sostenido (CAGR histórico 8.6%), que ambos métodos proyectan que continuará en 2026–2027 con alta concordancia; se recomienda presupuestar sobre la base de ~17,438 MWh y ~US$3.68 millones en 2027 (promedio de los métodos MLR y tarifa ASEP calibrada, los dos más consistentes entre sí), con el escenario SARIMA (~US$3.86 millones) como límite superior de sensibilidad."),
        bullet("La demanda pico podría acercarse a 5,200–5,300 kW en 2027. La tarifa MTD/BTD no cobra por capacidad contratada: cobra por la demanda máxima registrada en un solo intervalo de 10-15 minutos dentro del mes. Se recomienda monitorear y escalonar el arranque de cargas de alta potencia (climatización, laboratorios) para evitar que coincidan en el mismo intervalo y disparen el cargo mensual completo."),
        bullet("La tarifa efectiva no sigue una tendencia estadística porque está gobernada por decisiones regulatorias documentadas (fallo de la Corte Suprema de Justicia en 2024–2025 y resoluciones ASEP de ajuste tarifario), no por ruido; su proyección (≈$0.21/kWh) debe actualizarse en cuanto ASEP publique un nuevo pliego."),
        bullet("Aun calculando la tarifa exactamente medidor por medidor (sección 3.4), el importe real facturado es sistemáticamente menor al que implicaría la estructura tarifaria oficial: 3.7% antes de julio de 2025, y 13-23% después, con una brecha que se achica mes a mes. Esto sugiere que la UTP recibe algún tratamiento tarifario institucional o gubernamental no documentado en el pliego comercial; se recomienda solicitar a la oficina de servicios administrativos la confirmación de este tratamiento para sustentar formalmente el factor de calibración usado (0.842)."),
        bullet("Se recomienda repetir este ejercicio trimestralmente incorporando los datos reales más recientes. Ya se cuenta con el mapeo medidor-por-medidor (sede, distribuidora, tarifa) usado en la sección 3.4; el siguiente paso natural es extender los métodos 1 y 2 (hoy calculados a nivel institucional) a un pronóstico independiente por sede, lo que permitiría identificar cuáles sedes específicas impulsan el crecimiento proyectado."),

        h1("Anexo A. Reproducibilidad: datos, código y documentos fuente", "A."),
        h1Spacer(),
        p("Todo el análisis de este informe es reproducible. El repositorio del proyecto contiene:"),
        bullet("Datos: el CSV crudo de facturación (2021–2026), el listado oficial de los 65 medidores de la UTP (sede, distribuidora, tarifa asignada), el pliego tarifario oficial de ASEP (Excel resumido y PDF original de la resolución), y el CSV mensual agregado que consumen los modelos."),
        bullet("Código: 7 scripts de Python documentados (limpieza de datos, Método 1 – MLR, Método 2 – SARIMA Airline, backtesting/validación, Método 3 – calibración tarifaria, desglose energía/demanda, y el motor de cálculo tarifario exacto por medidor), más un script maestro que corre todo el pipeline en un solo comando y reproduce exactamente las cifras de este informe."),
        bullet("Documentos: este informe técnico y el resumen ejecutivo, en Word."),
        bullet("README con instrucciones de instalación (requirements.txt) y ejecución."),
        p("Repositorio del proyecto: [ enlace pendiente de publicar — ver nota de entrega ]. El paquete completo (datos + código + documentos) fue entregado junto con este informe como archivo comprimido para que el equipo lo suba a GitHub, Drive o el repositorio institucional que corresponda."),

        h1("Referencias", null),
        h1Spacer(),
        new Paragraph({ numbering: { reference: "refs-num", level: 0 }, spacing: { after: 120 },
          children: [new TextRun({ text: "Kialashaki, A., & Reisel, J. R. (2013). Modeling of the energy demand of the residential sector in the United States using regression models and artificial neural networks. Applied Energy, 108, 271–280.", size: 20 })] }),
        new Paragraph({ numbering: { reference: "refs-num", level: 0 }, spacing: { after: 120 },
          children: [new TextRun({ text: "Box, G. E. P., & Jenkins, G. M. (1976). Time Series Analysis: Forecasting and Control (2nd ed.). Holden-Day. (Identificación del modelo SARIMA(0,1,1)(0,1,1)₁₂, conocido como “modelo Airline”).", size: 20 })] }),
        new Paragraph({ numbering: { reference: "refs-num", level: 0 }, spacing: { after: 120 },
          children: [new TextRun({ text: "Hyndman, R. J., & Athanasopoulos, G. (2021). Forecasting: Principles and Practice (3rd ed.). OTexts: Melbourne, Australia. OTexts.com/fpp3.", size: 20 })] }),
        new Paragraph({ numbering: { reference: "refs-num", level: 0 }, spacing: { after: 120 },
          children: [new TextRun({ text: "U.S. Energy Information Administration (EIA). Annual Energy Outlook — metodología de modelos econométricos de demanda sectorial (National Energy Modeling System, NEMS).", size: 20 })] }),
        new Paragraph({ numbering: { reference: "refs-num", level: 0 }, spacing: { after: 120 },
          children: [new TextRun({ text: "Base de datos interna: registros de facturación eléctrica por medidor, Universidad Tecnológica de Panamá, enero 2022 – mayo 2026; y listado oficial de medidores (sede, distribuidora, tarifa asignada), consultado en agosto de 2026.", size: 20 })] }),
        new Paragraph({ numbering: { reference: "refs-num", level: 0 }, spacing: { after: 120 },
          children: [new TextRun({ text: "Autoridad Nacional de los Servicios Públicos (ASEP), Panamá. Pliegos tarifarios de EDEMET, ENSA y EDECHI 2023–2026: Resoluciones AN No. 18090-Elec, 18526-Elec, 18702-Elec, 18868-Elec, 19120-Elec, 19632-Elec, 19700-Elec, 19850-Elec y 19990-Elec.", size: 20 })] }),
      ],
    },
  ],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("../docs/informe_proyeccion_energia_UTP.docx", buf);
  console.log("OK");
});
