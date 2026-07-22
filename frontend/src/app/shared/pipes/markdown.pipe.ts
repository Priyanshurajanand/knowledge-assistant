import { Pipe, PipeTransform, inject } from '@angular/core';
import { DomSanitizer, SafeHtml } from '@angular/platform-browser';

@Pipe({
  name: 'markdown',
  standalone: true
})
export class MarkdownPipe implements PipeTransform {
  private sanitizer = inject(DomSanitizer);

  transform(value: string | null | undefined): SafeHtml {
    if (!value) return '';

    let html = value;

    // 1. Clean HTML characters to prevent XSS
    html = html
      .replace(/&/g, '&amp;')
      .replace(/</g, '&lt;')
      .replace(/>/g, '&gt;');

    // Remove inline source tags like (Source File: ... | Page: ...) or Source File: ...
    html = html.replace(/\(Source File:[^\)]+\)/gi, '');
    html = html.replace(/Source File:\s*[^\|\n]+\|\s*Page:\s*\d+/gi, '');

    // 2. Code blocks: ```language ... ```
    html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
      const languageClass = lang ? ` class="language-${lang}"` : '';
      return `<pre><code${languageClass}>${code.trim()}</code></pre>`;
    });

    // 3. Inline code: `code`
    html = html.replace(/`([^`]+)`/g, '<code>$1</code>');

    // 4. Bold text: **text**
    html = html.replace(/\*\*([^*]+)\*\*/g, '<strong>$1</strong>');

    // 5. Italic text: *text*
    html = html.replace(/\*([^*]+)\*/g, '<em>$1</em>');

    // 6. Headers
    html = html.replace(/^### (.*$)/gim, '<h3>$1</h3>');
    html = html.replace(/^## (.*$)/gim, '<h2>$1</h2>');
    html = html.replace(/^# (.*$)/gim, '<h1>$1</h1>');

    // 7. Unordered lists: - item
    html = html.replace(/^\s*-\s+(.*)$/gim, '<li>$1</li>');
    html = html.replace(/(<li>.*<\/li>)/gim, '<ul>$1</ul>');
    // Clean nested lists formatting duplicates
    html = html.replace(/<\/ul>\s*<ul>/g, '');

    // 8. Paragraphs and line breaks
    const lines = html.split(/\n\n+/);
    const parsedLines = lines.map(line => {
      const trimmed = line.trim();
      if (!trimmed) return '';
      if (
        trimmed.startsWith('<h') || 
        trimmed.startsWith('<pre') || 
        trimmed.startsWith('<ul') || 
        trimmed.startsWith('<li') || 
        trimmed.startsWith('<ol')
      ) {
        return trimmed;
      }
      return `<p>${trimmed.replace(/\n/g, '<br>')}</p>`;
    });

    html = parsedLines.join('\n');

    return this.sanitizer.bypassSecurityTrustHtml(html);
  }
}
