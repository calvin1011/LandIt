package main

import (
	"encoding/json"
	"fmt"
	"html"
	"strings"
)

func exportPreview(payload ExportPayload) ([]byte, string, error) {
	tpl := getTemplate(payload)
	var sb strings.Builder
	switch tpl {
	case "modern":
		renderHTMLModern(payload, &sb)
	case "minimal":
		renderHTMLMinimal(payload, &sb)
	default:
		renderHTMLClassic(payload, &sb)
	}
	out := map[string]string{"html": sb.String()}
	data, err := json.Marshal(out)
	if err != nil {
		return nil, "", err
	}
	return data, "application/json", nil
}

func renderHTMLClassic(payload ExportPayload, w *strings.Builder) {
	w.WriteString(`<div style="font-family:Helvetica,Arial,sans-serif;max-width:700px;margin:0 auto;padding:1rem;font-size:14px;">`)
	pi := payload.PersonalInfo
	name := strings.TrimSpace(pi.Name)
	if name != "" {
		w.WriteString(fmt.Sprintf("<h1 style=\"margin:0 0 0.5rem 0;font-size:1.5rem;\">%s</h1>", html.EscapeString(name)))
	}
	contactParts := []string{}
	if pi.Email != "" {
		contactParts = append(contactParts, html.EscapeString(pi.Email))
	}
	if pi.Phone != "" {
		contactParts = append(contactParts, html.EscapeString(pi.Phone))
	}
	if pi.Location != "" {
		contactParts = append(contactParts, html.EscapeString(pi.Location))
	}
	if len(contactParts) > 0 {
		w.WriteString(fmt.Sprintf("<p style=\"margin:0 0 1rem 0;color:#444;\">%s</p>", strings.Join(contactParts, " | ")))
	}
	if payload.Summary != "" {
		w.WriteString("<h2 style=\"font-size:1.1rem;margin:1rem 0 0.25rem 0;\">Summary</h2>")
		w.WriteString(fmt.Sprintf("<p style=\"margin:0;\">%s</p>", html.EscapeString(payload.Summary)))
	}
	if len(payload.WorkExperience) > 0 {
		w.WriteString("<h2 style=\"font-size:1.1rem;margin:1rem 0 0.25rem 0;\">Work Experience</h2>")
		for _, exp := range payload.WorkExperience {
			titleCompany := html.EscapeString(strings.TrimSpace(exp.Title))
			if exp.Company != "" {
				titleCompany += " at " + html.EscapeString(strings.TrimSpace(exp.Company))
			}
			w.WriteString(fmt.Sprintf("<p style=\"margin:0.25rem 0;font-weight:bold;\">%s</p>", titleCompany))
			dateStr := exp.StartDate
			if exp.EndDate != "" {
				dateStr += " - " + exp.EndDate
			}
			if dateStr != "" {
				w.WriteString(fmt.Sprintf("<p style=\"margin:0 0 0.25rem 0;font-size:0.9rem;color:#555;\">%s</p>", html.EscapeString(dateStr)))
			}
			w.WriteString("<ul style=\"margin:0 0 0.5rem 1rem;padding:0;\">")
			for _, b := range exp.Bullets {
				if b != "" {
					w.WriteString(fmt.Sprintf("<li>%s</li>", html.EscapeString(b)))
				}
			}
			w.WriteString("</ul>")
		}
	}
	if len(payload.Education) > 0 {
		w.WriteString("<h2 style=\"font-size:1.1rem;margin:1rem 0 0.25rem 0;\">Education</h2>")
		for _, edu := range payload.Education {
			line := html.EscapeString(strings.TrimSpace(edu.Degree))
			if edu.Field != "" {
				line += " in " + html.EscapeString(strings.TrimSpace(edu.Field))
			}
			if edu.School != "" {
				line += ", " + html.EscapeString(strings.TrimSpace(edu.School))
			}
			if line != "" {
				w.WriteString(fmt.Sprintf("<p style=\"margin:0.25rem 0;\">%s</p>", line))
			}
		}
	}
	if len(payload.Skills) > 0 {
		w.WriteString("<h2 style=\"font-size:1.1rem;margin:1rem 0 0.25rem 0;\">Skills</h2>")
		for cat, skills := range payload.Skills {
			if cat == "" {
				cat = "Other"
			}
			var parts []string
			for _, s := range skills {
				if s != "" {
					parts = append(parts, html.EscapeString(strings.TrimSpace(s)))
				}
			}
			if len(parts) > 0 {
				w.WriteString(fmt.Sprintf("<p style=\"margin:0.25rem 0;\">%s: %s</p>", html.EscapeString(cat), strings.Join(parts, ", ")))
			}
		}
	}
	if len(payload.Certifications) > 0 {
		w.WriteString("<h2 style=\"font-size:1.1rem;margin:1rem 0 0.25rem 0;\">Certifications</h2><ul style=\"margin:0 0 0 1rem;padding:0;\">")
		for _, c := range payload.Certifications {
			if c != "" {
				w.WriteString(fmt.Sprintf("<li>%s</li>", html.EscapeString(strings.TrimSpace(c))))
			}
		}
		w.WriteString("</ul>")
	}
	w.WriteString("</div>")
}

func renderHTMLModern(payload ExportPayload, w *strings.Builder) {
	renderHTMLClassic(payload, w)
}

func renderHTMLMinimal(payload ExportPayload, w *strings.Builder) {
	renderHTMLClassic(payload, w)
}
