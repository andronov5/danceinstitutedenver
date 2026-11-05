"""Render unchanged testimonial copy as a progressively enhanced sliding gallery."""

from html import escape


def render_reviews(quotes):
    """Return the Home reviews section for an ordered sequence of (quote, author)."""
    quotes = list(quotes)
    if not quotes:
        return ""
    panels = "".join(
        f'''<figure class="review-panel" id="gallery-review-{index}" data-review-slide>
          <blockquote>{escape(quote)}</blockquote><figcaption>{escape(author)}</figcaption>
        </figure>'''
        for index, (quote, author) in enumerate(quotes)
    )
    dots = "".join(
        f'<button class="review-dot" type="button" data-review-dot="{index}" aria-controls="gallery-review-{index}" aria-label="Show review by {escape(author, quote=True)}" aria-pressed="{str(index == 0).lower()}"></button>'
        for index, (_, author) in enumerate(quotes)
    )
    return f'''<section class="testimonials review-gallery" data-review-gallery aria-labelledby="testimonials-title">
      <div class="review-heading section-shell"><h2 id="testimonials-title">What Our <em>Students Say</em></h2></div>
      <div class="review-viewport"><div class="review-rail" aria-live="off">{panels}</div></div>
      <div class="review-navigation section-shell">
        <button class="review-arrow" type="button" data-review-prev aria-label="Previous testimonial"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M19 12H5m7-7-7 7 7 7"/></svg></button>
        <div class="review-dots" aria-label="Choose a review">{dots}</div>
        <button class="review-arrow" type="button" data-review-next aria-label="Next testimonial"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.4" aria-hidden="true"><path d="M5 12h14m-7-7 7 7-7 7"/></svg></button>
      </div>
      <p class="review-status" aria-live="polite" aria-atomic="true"></p>
    </section>'''
