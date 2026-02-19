package main

import (
	"bytes"
	"fmt"
	"strings"

	"github.com/jung-kurt/gofpdf/v2"
)

const marginMM = 19.05

func exportPDF(payload ExportPayload) ([]byte, string, error) {
	tpl := getTemplate(payload)
	var buf bytes.Buffer
	var err error
	switch tpl {
	case "modern":
		err = renderPDFModern(payload, &buf)
	case "minimal":
		err = renderPDFMinimal(payload, &buf)
	default:
		err = renderPDFClassic(payload, &buf)
	}
	if err != nil {
		return nil, "", err
	}
	return buf.Bytes(), "application/pdf", nil
}

func renderPDFClassic(payload ExportPayload, w *bytes.Buffer) error {
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

	if payload.Summary != "" {
		pdf.SetFont("Helvetica", "B", 11)
		pdf.CellFormat(0, 6, "Summary", "", 1, "L", false, 0, "")
		pdf.SetFont("Helvetica", "", 10)
		pdf.MultiCell(0, 5, payload.Summary, "", "L", false)
		pdf.Ln(4)
	}

	if len(payload.WorkExperience) > 0 {
		pdf.SetFont("Helvetica", "B", 11)
		pdf.CellFormat(0, 6, "Work Experience", "", 1, "L", false, 0, "")
		pdf.SetFont("Helvetica", "", 10)
		for _, exp := range payload.WorkExperience {
			titleCompany := strings.TrimSpace(exp.Title)
			if exp.Company != "" {
				titleCompany += " at " + strings.TrimSpace(exp.Company)
			}
			pdf.SetFont("Helvetica", "B", 10)
			pdf.CellFormat(0, 5, titleCompany, "", 1, "L", false, 0, "")
			pdf.SetFont("Helvetica", "", 9)
			dateStr := exp.StartDate
			if exp.EndDate != "" {
				dateStr += " - " + exp.EndDate
			}
			if dateStr != "" {
				pdf.CellFormat(0, 4, dateStr, "", 1, "L", false, 0, "")
			}
			for _, b := range exp.Bullets {
				if b == "" {
					continue
				}
				pdf.CellFormat(5, 4, "-", "", 0, "L", false, 0, "")
				pdf.MultiCell(0, 4, b, "", "L", false)
			}
			pdf.Ln(2)
		}
		pdf.Ln(2)
	}

	if len(payload.Education) > 0 {
		pdf.SetFont("Helvetica", "B", 11)
		pdf.CellFormat(0, 6, "Education", "", 1, "L", false, 0, "")
		pdf.SetFont("Helvetica", "", 10)
		for _, edu := range payload.Education {
			line := strings.TrimSpace(edu.Degree)
			if edu.Field != "" {
				line += " in " + strings.TrimSpace(edu.Field)
			}
			if edu.School != "" {
				line += ", " + strings.TrimSpace(edu.School)
			}
			if line != "" {
				pdf.CellFormat(0, 5, line, "", 1, "L", false, 0, "")
			}
		}
		pdf.Ln(2)
	}

	if len(payload.Skills) > 0 {
		pdf.SetFont("Helvetica", "B", 11)
		pdf.CellFormat(0, 6, "Skills", "", 1, "L", false, 0, "")
		pdf.SetFont("Helvetica", "", 10)
		for cat, skills := range payload.Skills {
			if cat == "" {
				cat = "Other"
			}
			var parts []string
			for _, s := range skills {
				if s != "" {
					parts = append(parts, strings.TrimSpace(s))
				}
			}
			if len(parts) > 0 {
				pdf.CellFormat(0, 5, fmt.Sprintf("%s: %s", cat, strings.Join(parts, ", ")), "", 1, "L", false, 0, "")
			}
		}
		pdf.Ln(2)
	}

	if len(payload.Certifications) > 0 {
		pdf.SetFont("Helvetica", "B", 11)
		pdf.CellFormat(0, 6, "Certifications", "", 1, "L", false, 0, "")
		pdf.SetFont("Helvetica", "", 10)
		for _, c := range payload.Certifications {
			if c != "" {
				pdf.CellFormat(0, 5, "- "+strings.TrimSpace(c), "", 1, "L", false, 0, "")
			}
		}
	}

	return pdf.Output(w)
}

func renderPDFModern(payload ExportPayload, w *bytes.Buffer) error {
	return renderPDFClassic(payload, w)
}

func renderPDFMinimal(payload ExportPayload, w *bytes.Buffer) error {
	return renderPDFClassic(payload, w)
}
