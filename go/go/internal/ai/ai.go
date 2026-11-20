// Package ai enthält die Operation ai.ask. Die Werkzeuge kommen unverändert aus der Operationsbeschreibung
// (Registry.Tools); vorgeschlagene Aufrufe werden nicht ausgeführt.
package ai

import (
	"context"
	"encoding/json"
	"fmt"
	"log/slog"
	"time"

	"github.com/anthropics/anthropic-sdk-go"
	"github.com/anthropics/anthropic-sdk-go/option"

	"chronos/internal/notify"
	"chronos/internal/op"
)

type AskParams struct {
	Prompt string  `json:"prompt" minLength:"1" doc:"Frage oder Auftrag an den Assistenten"`
	TeamID *string `json:"team_id,omitempty" format:"uuid" doc:"Team, auf das sich die Frage bezieht"`
}
type ProposedCall struct {
	Name  string         `json:"name" doc:"Operationsname mit Punkt, z. B. appointment.create"`
	Input map[string]any `json:"input"`
}
type Usage struct {
	InputTokens  int64 `json:"input_tokens"`
	OutputTokens int64 `json:"output_tokens"`
}
type AskResult struct {
	Text          string         `json:"text"`
	ProposedCalls []ProposedCall `json:"proposed_calls"`
	Usage         Usage          `json:"usage"`
}

func Register(r *op.Registry) {
	op.Register(r, op.Op{Name: "ai.ask",
		Description: "Fragt die KI (Anthropic Messages API) mit den Chronos-Werkzeugen; vorgeschlagene Aufrufe werden nicht ausgeführt."},
		func(c *op.Ctx, p AskParams) (AskResult, error) {
			if p.TeamID != nil {
				id, err := op.ParseID(*p.TeamID, "team_id")
				if err != nil {
					return AskResult{}, err
				}
				if err := c.RequireMember(id); err != nil {
					return AskResult{}, err
				}
			}
			return ask(c, r, p)
		})
}

func ask(c *op.Ctx, r *op.Registry, p AskParams) (AskResult, error) {
	cfg := c.Cfg
	opts := []option.RequestOption{option.WithAPIKey(cfg.AnthropicAPIKey), option.WithMaxRetries(0), option.WithRequestTimeout(60 * time.Second)}
	if cfg.AnthropicBaseURL != "" {
		opts = append(opts, option.WithBaseURL(cfg.AnthropicBaseURL))
	}
	client := anthropic.NewClient(opts...)

	var tools []anthropic.ToolUnionParam
	for _, t := range r.Tools() {
		schema := anthropic.ToolInputSchemaParam{Properties: t.InputSchema["properties"], ExtraFields: map[string]any{}}
		if req, ok := t.InputSchema["required"].([]any); ok {
			for _, s := range req {
				schema.Required = append(schema.Required, fmt.Sprint(s))
			}
		}
		if v, ok := t.InputSchema["additionalProperties"]; ok {
			schema.ExtraFields["additionalProperties"] = v
		}
		tools = append(tools, anthropic.ToolUnionParam{OfTool: &anthropic.ToolParam{Name: t.Name, Description: anthropic.String(t.Description), InputSchema: schema}})
	}
	system := "Du bist der Assistent von Chronos, einer Terminverwaltung für Teams. Nutze die bereitgestellten Werkzeuge, um Aufrufe vorzuschlagen; sie werden nicht automatisch ausgeführt. Zeitpunkte gibst du in UTC an (ISO 8601 mit Z)."
	if p.TeamID != nil {
		system += " Aktuelles Team: " + *p.TeamID + "."
	}
	ctx, cancel := context.WithTimeout(c.Context, 60*time.Second)
	defer cancel()
	msg, err := client.Messages.New(ctx, anthropic.MessageNewParams{
		Model:     anthropic.Model(cfg.AnthropicModel),
		MaxTokens: 1024,
		System:    []anthropic.TextBlockParam{{Text: system}},
		Messages:  []anthropic.MessageParam{anthropic.NewUserMessage(anthropic.NewTextBlock(p.Prompt))},
		Tools:     tools,
	})
	if err != nil {
		slog.ErrorContext(c.Context, "KI-Aufruf fehlgeschlagen", "error", err.Error())
		return AskResult{}, op.Provider("KI-Anbieter: %v", err)
	}
	res := AskResult{ProposedCalls: []ProposedCall{}, Usage: Usage{InputTokens: msg.Usage.InputTokens, OutputTokens: msg.Usage.OutputTokens}}
	for _, b := range msg.Content {
		switch b.Type {
		case "text":
			res.Text += b.Text
		case "tool_use":
			name, ok := r.OperationName(b.Name)
			if !ok {
				continue
			}
			in := map[string]any{}
			if err := json.Unmarshal(b.Input, &in); err != nil {
				continue
			}
			res.ProposedCalls = append(res.ProposedCalls, ProposedCall{Name: name, Input: in})
		}
	}
	amount := (res.Usage.InputTokens*cfg.AIPriceInMicro + res.Usage.OutputTokens*cfg.AIPriceOutMicro + 500000) / 1000000
	err = notify.RecordCost(c, "anthropic", map[string]any{"input_tokens": res.Usage.InputTokens, "output_tokens": res.Usage.OutputTokens}, amount)
	return res, err
}
