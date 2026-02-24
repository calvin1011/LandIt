package main

import (
	"bytes"
	"strings"

	"github.com/jung-kurt/gofpdf/v2"
)

func exportCoverLetterPDF(payload CoverLetterPayload) ([]byte, string, error) {
	var buf bytes.Buffer
	if err := renderCoverLetterPDF(payload, &buf); err != nil {
		return nil, "", err
	}
	return buf.Bytes(), "application/pdf", nil
}

func renderCoverLetterPDF(payload CoverLetterPayload, w *bytes.Buffer) error {
	pdf := gofpdf.New("P", "mm", "A4", "")
	pdf.SetMargins(marginMM, marginMM, marginMM)
	pdf.SetAutoPageBreak(true, marginMM)
	pdf.AddPage()
	pdf.SetFont("Helvetica", "", 11)

	pi := payload.PersonalInfo
	name := strings.TrimSpace(pi.Name)
	if name != "" {
		pdf.SetFont("Helvetica", "B", 14)
		pdf.CellFormat(0, 8, name, "", 1, "L", false, 0, "")
		pdf.SetFont("Helvetica", "", 10)
	}
	contactParts := []string{}
	if pi.Email != "" {
		contactParts = append(contactParts, pi.Email)
	}
	if pi.Phone != "" {
		contactParts = append(contactParts, pi.Phone)
	}
	if pi.Location != "" {
		contactParts = append(contactParts, pi.Location)
	}
	if len(contactParts) > 0 {
		pdf.CellFormat(0, 6, strings.Join(contactParts, " | "), "", 1, "L", false, 0, "")
	}
	pdf.Ln(4)

	for _, p := range payload.Paragraphs {
		p = strings.TrimSpace(p)
		if p == "" {
			continue
		}
		pdf.SetFont("Helvetica", "", 10)
		pdf.MultiCell(0, 5, p, "", "L", false)
		pdf.Ln(2)
	}

	return pdf.Output(w)
}
