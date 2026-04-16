# 🤖 API Specialist Worker

Especialista em design, desenvolvimento e documentação de APIs RESTful e GraphQL.

## 📋 Visão Geral

Este worker é um agente especializado com expertise em:

- 🌐 **Design de APIs RESTful** - Princípios REST, HATEOAS, status codes
- 📊 **GraphQL** - Schemas, resolvers, mutations, subscriptions
- 📖 **Documentação OpenAPI/Swagger** - Especificações 3.0+, Swagger UI
- 🔐 **Autenticação e Autorização** - JWT, OAuth 2.0, API Keys, RBAC/ABAC
- 🏷️ **Versionamento de APIs** - Estratégias de versionamento e depreciação
- ⚡ **Rate Limiting e Throttling** - Algoritmos, circuit breakers
- 🧪 **Testing de APIs** - Unitário, integração, contrato, performance
- 🚀 **Frameworks Populares** - FastAPI, Flask, Express, Django REST, NestJS

## 📁 Estrutura

```
api-specialist/
├── worker.yaml      # Configuração do worker
├── prompt.txt      # System prompt especializado
└── README.md       # Este arquivo
```

## 🚀 Uso

### Configuração (worker.yaml)

```yaml
metadata:
  name: api-specialist
  version: 1.0.0
  category: backend
  
spec:
  expertise:
    - Design de APIs RESTful (expert)
    - GraphQL (expert)
    - OpenAPI/Swagger (expert)
    - Autenticação/Autorização (expert)
    - Versionamento (advanced)
    - Rate Limiting (advanced)
    - Testing (expert)
    - Frameworks Populares (expert)
```

### Prompt Especializado (prompt.txt)

O system prompt inclui:
- Diretrizes detalhadas para cada área de expertise
- Princípios de segurança
- Padrões de documentação
- Padrões de teste
- Boas práticas de performance
- Estrutura de resposta padronizada

## 🛡️ Segurança

O worker segue princípios rigorosos de segurança:
- HTTPS sempre
- Validação rigorosa de inputs
- Sanitização contra injection attacks
- Rate limiting
- CORS adequado
- Principle of least privilege
- Audit logging

## 🧪 Testing

Recomendações de cobertura de testes:
- Unitários (mínimo 80%)
- Integração para todos endpoints
- Autenticação/autorização
- Rate limiting
- Validação de input

## 📚 Documentação

Para cada API criada, o worker fornece:
- Especificação OpenAPI 3.0+ completa
- README.md com instruções
- Collection Postman
- CHANGELOG.md

## 🎯 Casos de Uso

- Criar APIs RESTful do zero
- Migrar APIs para GraphQL
- Implementar autenticação segura
- Documentar APIs existentes
- Revisar segurança de APIs
- Otimizar performance de APIs
- Criar testes automatizados

## 🔧 Frameworks Suportados

| Linguagem | Frameworks |
|-----------|------------|
| Python | FastAPI, Flask, Django REST |
| JavaScript | Express.js, NestJS, Fastify |
| TypeScript | NestJS, Express.js, Fastify |
| Java | Spring Boot, JAX-RS |
| Go | Gin, Echo, Fiber |
| Rust | Actix-web, Axum, Rocket |

## 📄 Licença

Parte do ecossistema de workers especializados.
