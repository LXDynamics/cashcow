# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

This is a **Docusaurus-based documentation site** for CashCow, a comprehensive Python-based cash flow modeling system for businesses. The site serves as the central documentation hub containing guides, tutorials, examples, and technical references.

## Common Development Commands

### Core Development
```bash
# Install dependencies
npm run

# Start development server with hot reload
npm run start

# Build static site for production
npm run build

# Serve built site locally
npm run serve

# Type checking
npm run typecheck

# Clear Docusaurus cache
npm run clear
```

### Deployment
```bash
# Deploy to GitHub Pages (with SSH)
USE_SSH=true npm run deploy

# Deploy to GitHub Pages (without SSH)
GIT_USER=<username> npm run deploy
```

## Architecture & Structure

### Documentation Organization
- **`docs/`** - Core documentation in Markdown/MDX format
  - Main guides: `GETTING_STARTED.md`, `CLI_REFERENCE.md`, `TROUBLESHOOTING.md`
  - Architecture documentation: `ARCHITECTURE_ANALYSIS.md`, `ARCHITECTURE_SUMMARY.md`
  - Feature guides: `ENTITIES_GUIDE.md`, `CALCULATION_ENGINE_GUIDE.md`, `REPORTS_GUIDE.md`
  - Visual documentation in `diagrams/` subdirectories
  - Working examples in `examples/` with YAML configurations

### Site Structure
- **`src/`** - React components and custom CSS
- **`static/`** - Static assets (images, favicons)
- **`blog/`** - Blog posts (currently contains default Docusaurus examples)
- **`docusaurus.config.ts`** - Main site configuration
- **`sidebars.ts`** - Navigation structure (auto-generated from docs folder)

### Key Configuration Files
- **`package.json`** - Dependencies and scripts for npm run-based workflow
- **`tsconfig.json`** - TypeScript configuration
- **`docusaurus.config.ts`** - Site metadata, themes, plugins, and deployment settings

## Content Guidelines

### Documentation Content Focus
This site documents a **financial modeling CLI tool** (`cashcow`) with:
- Entity-based data modeling (employees, grants, facilities, etc.)
- Cash flow forecasting and KPI tracking
- Plugin-based calculation system
- Multiple export formats and analysis tools
- Business-specific features and customizations

### Mermaid Diagram Support
The site has **Mermaid diagram rendering** enabled via `@docusaurus/theme-mermaid`:
- Use standard Mermaid syntax in fenced code blocks: `````mermaid`
- Supported diagram types: flowcharts, sequence diagrams, class diagrams, etc.
- Diagrams are rendered client-side with interactive features
- Example: See `docs/test-mermaid.md` for syntax examples

### Working with Documentation
- All main documentation is in `docs/` directory
- Use Markdown/MDX format for content
- Reference diagrams are in `docs/diagrams/` subdirectories
- Example configurations are in `docs/examples/` with YAML files
- The sidebar is auto-generated from the folder structure

### Content Architecture
The documentation follows a comprehensive structure:
1. **Getting Started** - Installation and first model tutorial  
2. **Technical References** - CLI commands, entities, calculations, reports
3. **Architecture Documentation** - System design and technical deep-dives
4. **Visual Documentation** - Mermaid diagrams showing workflows and relationships
5. **Examples & Tutorials** - Ready-to-use configurations and scenarios

## Development Notes

### Technology Stack
- **Docusaurus 3.8.1** - Static site generator
- **React 19** - Component framework
- **TypeScript** - Type safety
- **MDX** - Enhanced Markdown with React components

### File Patterns
- Documentation files use `.md` or `.mdx` extensions
- Configuration files use `.yaml` for examples
- Diagrams reference `.mmd` files (Mermaid syntax)
- All paths in documentation assume the CashCow CLI tool is installed via Poetry

### Content Maintenance
- The site documents an external Python CLI tool, not web application code
- Focus on user-facing features and workflows rather than implementation details
- Keep examples current with the CLI tool's capabilities
- Maintain consistency between getting started guide and detailed references