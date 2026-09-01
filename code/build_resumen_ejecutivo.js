const fs = require("fs");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, Table, TableRow, TableCell,
  WidthType, ShadingType, BorderStyle, AlignmentType, ImageRun, Footer,
  VerticalAlign,
} = require("docx");

const TEAL = "4D8270";
const SAGE = "6DA894";
const PURPLE = "4C2E6A";
const GOLD = "B8860B";
const DARKGREEN = "244E38";
const LIGHTGRAY = "F2F2F2";
const LIGHTGREEN_TINT = "EEF3F0";
const GRAY = "5c6163";

function p(text, opts = {}) {
  return new Paragraph({ spacing: { after: 80, line: 240 }, children: [new TextRun({ text, ...opts })] });
}
function bullet(text) {
  return new Paragraph({ text, bullet: { level: 0 }, spacing: { after: 50 } });
}

function kpiCard(label, value, sub, valueColor) {
  // Tarjeta KPI (spec 2C del sistema de diseño): tinte verde muy tenue,
  // borde superior sólido en verde, etiqueta gris, cifra grande en color.
  return new TableCell({
    width: { size: 3100, type: WidthType.DXA },
    shading: { type: ShadingType.CLEAR, fill: LIGHTGREEN_TINT },
    verticalAlign: VerticalAlign.CENTER,
    margins: { top: 120, bottom: 120, left: 170, right: 170 },
    borders: { top: { style: BorderStyle.SINGLE, size: 20, color: TEAL } },
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
        children: [new TextRun({ text: label, bold: true, size: 18, color: GRAY })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
        children: [new TextRun({ text: value, bold: true, size: 40, color: valueColor })] }),
      new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: sub, size: 16, color: GRAY })] }),
    ],
  });
}

function imagePar(path, width, height) {
  const data = fs.readFileSync(path);
  return new Paragraph({
    alignment: AlignmentType.CENTER,
    spacing: { before: 200, after: 80 },
    children: [new ImageRun({ data, transformation: { width, height }, type: "png" })],
  });
}

const doc = new Document({
  styles: {
    default: { document: { run: { font: "Calibri", size: 22 } } },
    paragraphStyles: [
      { id: "Heading1", name: "Heading 1", basedOn: "Normal", next: "Normal", quickFormat: true,
        run: { bold: true, size: 26, color: TEAL, font: "Calibri" },
        paragraph: { spacing: { before: 140, after: 70 } } },
    ],
  },
  sections: [{
    properties: { page: { size: { width: 12240, height: 15840 }, margin: { top: 0, bottom: 400, left: 1080, right: 1080 } } },
    footers: {
      default: new Footer({ children: [new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "Informe completo con metodología, validación y anexos: informe_proyeccion_energia_UTP.docx", size: 16, color: GRAY, italics: true })] })] }),
    },
    children: [
      // ---- Banda diagonal de encabezado (spec 2B: banda diagonal 15%) ----
      new Paragraph({
        spacing: { after: 40 },
        children: [ new ImageRun({
          data: fs.readFileSync("../figures/banner_diagonal.png"),
          transformation: { width: 850, height: 100 },
          type: "png",
        }) ],
      }),

      new Paragraph({ spacing: { before: 120, after: 0 }, alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: "UNIVERSIDAD TECNOLÓGICA DE PANAMÁ · DINAGEA", bold: true, size: 20, color: DARKGREEN })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 40 },
        children: [new TextRun({ text: "Proyección Energética 2026–2027", bold: true, size: 36 })] }),
      new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 180 },
        children: [new TextRun({ text: "Resumen ejecutivo · " + new Date().toLocaleDateString('es-PA', { year: 'numeric', month: 'long', day: 'numeric' }), italics: true, size: 18, color: GRAY })] }),

      p("Se proyectó el consumo, la demanda, la tarifa y el costo de energía eléctrica de todas las sedes de la UTP para 2026 y 2027, usando dos métodos estadísticos independientes y una validación adicional contra el pliego tarifario real de ASEP. Los tres enfoques coinciden dentro de un margen de 5%, lo que da alta confianza a la cifra recomendada."),

      new Table({
        width: { size: 9360, type: WidthType.DXA },
        borders: { top:{style:BorderStyle.NONE}, bottom:{style:BorderStyle.NONE}, left:{style:BorderStyle.NONE}, right:{style:BorderStyle.NONE}, insideHorizontal:{style:BorderStyle.NONE}, insideVertical:{style:BorderStyle.NONE} },
        rows: [ new TableRow({ children: [
          kpiCard("CONSUMO 2027", "17,438 MWh", "+13.4% vs. 2025", TEAL),
          kpiCard("DEMANDA PICO 2027", "5,225 kW", "+5.8% vs. 2025", TEAL),
          kpiCard("COSTO 2027", "US$3.68 M", "rango: $3.68M–$3.86M", PURPLE),
        ]}) ],
      }),

      new Paragraph({ spacing: { before: 140 } }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, text: "Evolución del costo anual" }),
      imagePar("../figures/fig_costo_anual.png", 410, 172),
      p("Barras verdes: costo real facturado (2022–2025). Barras de color: proyección 2026–2027 por cada uno de los tres métodos aplicados (estadístico, serie de tiempo, y tarifa real de ASEP).", { italics: true, size: 18, color: GRAY }),

      new Paragraph({ heading: HeadingLevel.HEADING_1, text: "Lectura para la toma de decisión" }),
      bullet("El consumo y el costo mantienen una tendencia de crecimiento sostenido (~8-9% anual) desde 2022; no es un pico aislado, es la trayectoria de los últimos 4 años."),
      bullet("Se recomienda presupuestar 2027 sobre US$3.68 millones, con US$3.86 millones como techo de contingencia."),
      bullet("Del costo total, ~76% es cargo por energía (kWh consumidos) y ~24% es cargo por demanda (el pico máximo de 10-15 minutos del mes). Esta proporción se ha mantenido estable desde 2023."),
      bullet("La demanda pico podría llegar a 5,200–5,300 kW. Esta tarifa no cobra por capacidad contratada sino por ese único pico máximo del mes; se recomienda escalonar el arranque de cargas grandes para evitar que coincidan en el mismo intervalo."),
      bullet("Se identificó que el importe real facturado es menor al que correspondería por tarifa comercial plena, lo que sugiere que la UTP tiene algún tratamiento tarifario especial. Se recomienda confirmarlo formalmente con la administración para sustentar la proyección de costo con mayor precisión."),

      new Paragraph({ heading: HeadingLevel.HEADING_1, text: "Respaldo de la proyección" }),
      p("La proyección se validó de dos formas antes de aceptarse: (1) se probó cada método prediciendo 2025 usando solo datos hasta 2024, comparando contra lo realmente ocurrido (error de 4.5% a 12%, según variable); (2) se contrastó contra el pliego tarifario oficial de ASEP, encontrándose que un fallo judicial de 2024-2025 explica gran parte de la variación tarifaria histórica. Detalle metodológico, código y datos fuente en el repositorio del proyecto y en el informe técnico adjunto.", { size: 20 }),
    ],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  fs.writeFileSync("../docs/resumen_ejecutivo_UTP.docx", buf);
  console.log("OK");
});
