// Learn more about clients at https://docs.boundaryml.com/docs/snippets/clients/overview

// Google AI Studio (Gemini) — primary client
// Uses the native google-ai provider
client<llm> Gemini {
  provider google-ai
  options {
    model "gemini-2.5-flash"
    api_key env.GOOGLE_API_KEY
  }
}

// Optional: Gemini via OpenAI-compatible endpoint
// Useful if you want to use more OpenAI-centric tooling
// client<llm> GeminiOpenAI {
//   provider openai-generic
//   options {
//     base_url "https://generativelanguage.googleapis.com/v1beta/openai"
//     model "gemini-2.5-flash"
//     api_key env.GOOGLE_API_KEY
//   }
// }

// Retry policies
retry_policy Exponential {
  max_retries 2
  strategy {
    type exponential_backoff
    delay_ms 300
    multiplier 1.5
    max_delay_ms 10000
  }
}