package main

import (
	"os"
	"strings"

	"github.com/gomutex/godocx"
)

const docxContentType = "application/vnd.openxmlformats-officedocument.wordprocessingml.document"

func exportDOCX(payload ExportPayload) ([]byte, string, error) {
	tpl := getTemplate(payload)
	var doc *godocx.Document
	var err error
	switch tpl {
	case "modern":
		doc, err = renderDOCXModern(payload)
	case "minimal":
		doc, err = renderDOCXMinimal(payload)
	default:
		doc, err = renderDOCXClassic(payload)
	}
	if err != nil {
		return nil, "", err
	}
	tmp, err := os.CreateTemp("", "landit-*.docx")
	if err != nil {
		return nil, "", err
	}
	path := tmp.Name()
	tmp.Close()
	defer os.Remove(path)
	if err := doc.SaveTo(path); err != nil {
		return nil, "", err
	}
	data, err := os.ReadFile(path)
	if err != nil {
		return nil, "", err
	}
	return data, docxContentType, nil
}

func renderDOCXClassic(payload ExportPayload) (*godocx.Document, error) {
	doc, err := godocx.NewDocument()
	if err != nil {
		return nil, err
	}

	pi := payload.PersonalInfo
	name := strings.TrimSpace(pi.Name)
	if name != "" {
		p := doc.AddParagraph(name)
		p.Style("Heading 1")
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
		doc.AddParagraph(strings.Join(contactParts, " | ")).Style("Normal")
	}

	if payload.Summary != "" {
		doc.AddParagraph("Summary").Style("Heading 1")
		doc.AddParagraph(payload.Summary).Style("Normal")
	}

	if len(payload.WorkExperience) > 0 {
		doc.AddParagraph("Work Experience").Style("Heading 1")
		for _, exp := range payload.WorkExperience {
			titleCompany := strings.TrimSpace(exp.Title)
			if exp.Company != "" {
				titleCompany += " at " + strings.TrimSpace(exp.Company)
			}
			doc.AddParagraph(titleCompany).Style("Normal")
			dateStr := exp.StartDate
			if exp.EndDate != "" {
				dateStr += " - " + exp.EndDate
			}
			if dateStr != "" {
				doc.AddParagraph(dateStr).Style("Normal")
			}
			for _, b := range exp.Bullets {
				if b != "" {
					doc.AddParagraph(b).Style("List Bullet")
				}
			}
		}
	}

	if len(payload.Education) > 0 {
		doc.AddParagraph("Education").Style("Heading 1")
		for _, edu := range payload.Education {
			line := strings.TrimSpace(edu.Degree)
			if edu.Field != "" {
				line += " in " + strings.TrimSpace(edu.Field)
			}
			if edu.School != "" {
				line += ", " + strings.TrimSpace(edu.School)
			}
			if line != "" {
				doc.AddParagraph(line).Style("Normal")
			}
		}
	}

	if len(payload.Skills) > 0 {
		doc.AddParagraph("Skills").Style("Heading 1")
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
				doc.AddParagraph(cat+": "+strings.Join(parts, ", ")).Style("Normal")
			}
		}
	}

	if len(payload.Certifications) > 0 {
		doc.AddParagraph("Certifications").Style("Heading 1")
		for _, c := range payload.Certifications {
			if c != "" {
				doc.AddParagraph(strings.TrimSpace(c)).Style("List Bullet")
			}
		}
	}

	return doc, nil
}

func renderDOCXModern(payload ExportPayload) (*godocx.Document, error) {
	return renderDOCXClassic(payload)
}

func renderDOCXMinimal(payload ExportPayload) (*godocx.Document, error) {
	return renderDOCXClassic(payload)
}
