"""
Book Generator Presentation Animation

This module creates animated presentations using Manim to explain and demonstrate
the book generator system architecture, workflow, and features. It provides
visual explanations of how the system works from high-level architecture to
detailed workflow steps.

Key responsibilities:
- System architecture visualization with component diagrams
- Book generation workflow animation showing step-by-step process
- Feature showcase with animated cards and descriptions
- Educational content explaining AI-powered book generation
- Visual demonstration of the complete system functionality
"""

from manim import *

class BookGeneratorExplanation(Scene):
    def construct(self):
        # Title scene
        title = Text("Book Generator with Google Gemini", font_size=48, color=BLUE)
        subtitle = Text("Automated Book Creation Using AI", font_size=32, color=TEAL)
        title.move_to(UP * 2)
        subtitle.move_to(UP * 0.5)

        self.play(Write(title))
        self.play(Write(subtitle))
        self.wait(2)

        # Overview
        overview = Text("An AI-powered Python application that generates complete books\nusing Google Gemini's advanced language model", font_size=24, color=WHITE)
        overview.move_to(DOWN * 1.5)

        self.play(FadeIn(overview))
        self.wait(3)
        self.play(FadeOut(title), FadeOut(subtitle), FadeOut(overview))

        # Architecture Scene
        self.show_architecture()

        # Flow Scene
        self.show_workflow()

        # Features Scene
        self.show_features()

        # Conclusion
        conclusion = Text("Book Generator: From Idea to Published Book in Minutes", font_size=36, color=YELLOW)
        conclusion.move_to(UP * 2)

        features_summary = BulletedList(
            "Dynamic Content Generation",
            "Flexible Table of Contents",
            "Markdown Output",
            "Command-line Interface",
            "Error Handling and Testing",
            font_size=24
        ).move_to(DOWN * 1)

        self.play(Write(conclusion))
        self.play(Write(features_summary))
        self.wait(4)
        self.play(FadeOut(conclusion), FadeOut(features_summary))

    def show_architecture(self):
        # Main components visualization
        title = Text("System Architecture", font_size=40, color=BLUE)
        title.to_edge(UP)

        # Create component boxes
        main_rect = Rectangle(width=3, height=0.8, color=BLUE, fill_opacity=0.2)
        main_text = Text("main.py", font_size=20).move_to(main_rect.get_center())

        config_rect = Rectangle(width=2.5, height=0.6, color=GREEN, fill_opacity=0.2)
        config_text = Text("config.py", font_size=16).move_to(config_rect.get_center())

        content_rect = Rectangle(width=3, height=0.6, color=PURPLE, fill_opacity=0.2)
        content_text = Text("content_generation.py", font_size=16).move_to(content_rect.get_center())

        book_gen_rect = Rectangle(width=3, height=0.6, color=RED, fill_opacity=0.2)
        book_gen_text = Text("book_generator.py", font_size=16).move_to(book_gen_rect.get_center())

        toc_rect = Rectangle(width=3, height=0.6, color=YELLOW, fill_opacity=0.2)
        toc_text = Text("table_of_contents.py", font_size=16).move_to(toc_rect.get_center())

        writer_rect = Rectangle(width=2.5, height=0.6, color=ORANGE, fill_opacity=0.2)
        writer_text = Text("book_writer.py", font_size=16).move_to(writer_rect.get_center())

        # Position components
        main_rect.move_to(UP * 1.5)
        config_rect.move_to(LEFT * 3 + UP * 0)
        content_rect.move_to(LEFT * 3 + DOWN * 1.5)
        book_gen_rect.move_to(ORIGIN + DOWN * 0.5)
        toc_rect.move_to(RIGHT * 3 + DOWN * 0)
        writer_rect.move_to(RIGHT * 3 + DOWN * 1.5)

        # Gemini API box
        gemini_rect = Rectangle(width=2.5, height=0.6, color=TEAL, fill_opacity=0.2)
        gemini_text = Text("Gemini API", font_size=16).move_to(gemini_rect.get_center())
        gemini_rect.move_to(DOWN * 2.5)

        # Arrows
        arrows = [
            Arrow(config_rect.get_right(), content_rect.get_right(), color=WHITE),
            Arrow(content_rect.get_right(), book_gen_rect.get_left(), color=WHITE),
            Arrow(book_gen_rect.get_right(), toc_rect.get_left(), color=WHITE),
            Arrow(book_gen_rect.get_right(), writer_rect.get_left(), color=WHITE),
            Arrow(content_rect.get_bottom(), gemini_rect.get_top(), color=WHITE),
            Arrow(writer_rect.get_left(), main_rect.get_bottom(), color=WHITE),
        ]

        # Labels
        labels = [
            Text("API Config", font_size=12, color=GREEN).next_to(config_rect, DOWN),
            Text("AI Content Generation", font_size=12, color=PURPLE).next_to(content_rect, DOWN),
            Text("Orchestrates Generation", font_size=12, color=RED).next_to(book_gen_rect, DOWN),
            Text("TOC Management", font_size=12, color=YELLOW).next_to(toc_rect, DOWN),
            Text("File Writing", font_size=12, color=ORANGE).next_to(writer_rect, DOWN),
            Text("External AI Service", font_size=12, color=TEAL).next_to(gemini_rect, DOWN),
        ]

        self.play(Write(title))
        self.play(Create(main_rect))
        self.play(Create(config_rect))
        self.play(Create(content_rect))
        self.play(Create(book_gen_rect))
        self.play(Create(toc_rect))
        self.play(Create(writer_rect))
        self.play(Create(gemini_rect))

        for arrow in arrows:
            self.play(Create(arrow))

        for label in labels:
            self.play(Write(label))

        self.wait(4)

        # Clear for next scene
        all_elements = [title, main_rect,  config_rect, 
                       content_rect,  book_gen_rect, 
                       toc_rect,  writer_rect, 
                       gemini_rect] + arrows + labels
        self.play(*[FadeOut(elem) for elem in all_elements])

    def show_workflow(self):
        title = Text("Book Generation Workflow", font_size=40, color=BLUE)
        title.to_edge(UP)

        # Workflow steps
        steps = [
            "1. User provides book title and TOC prompt",
            "2. Generate Table of Contents using Gemini",
            "3. Parse and validate TOC structure",
            "4. Generate chapter introductions",
            "5. Generate detailed subchapter content",
            "6. Write everything to Markdown file",
            "7. Save final book with navigation"
        ]

        step_texts = []
        for i, step in enumerate(steps):
            step_text = Text(step, font_size=20, color=WHITE)
            step_text.move_to(LEFT * 4 + UP * (2 - i * 0.6))
            step_texts.append(step_text)

        # Flow arrows
        arrows = []
        for i in range(len(step_texts) - 1):
            arrow = Arrow(
                step_texts[i].get_right(),
                step_texts[i + 1].get_left(),
                color=YELLOW
            )
            arrows.append(arrow)

        # Example output
        example_toc = Rectangle(width=3, height=2, color=GREEN, fill_opacity=0.1)
        example_toc.move_to(RIGHT * 3)
        example_title = Text("Generated TOC:", font_size=16, color=GREEN).move_to(RIGHT * 3 + UP * 1.2)
        example_content = Text("Chapter 1: Introduction\n  • Getting Started\n  • Prerequisites\nChapter 2: Core Concepts\n  • Main Components\n  • API Integration", font_size=12, color=WHITE).move_to(RIGHT * 3)

        self.play(Write(title))
        for text in step_texts:
            self.play(Write(text))
            self.wait(0.3)

        for arrow in arrows:
            self.play(Create(arrow))

        self.play(Create(example_toc), Write(example_title), Write(example_content))
        self.wait(4)

        # Clear scene
        all_elements = [title] + step_texts + arrows + [example_toc, example_title, example_content]
        self.play(*[FadeOut(elem) for elem in all_elements])

    def show_features(self):
        title = Text("Key Features", font_size=40, color=BLUE)
        title.to_edge(UP)

        features = [
            {
                "name": "Dynamic TOC Generation",
                "desc": "AI creates structured table of contents\nfrom user prompts",
                "color": GREEN
            },
            {
                "name": "Gemini Integration",
                "desc": "Uses Google's advanced language model\nfor high-quality content generation",
                "color": PURPLE
            },
            {
                "name": "Flexible Configuration",
                "desc": "Command-line interface with multiple\noptions and interactive editing",
                "color": BLUE
            },
            {
                "name": "Robust Error Handling",
                "desc": "Comprehensive error handling for API\nissues, file operations, and validation",
                "color": RED
            },
            {
                "name": "Markdown Output",
                "desc": "Generates clean, readable Markdown\nfiles with navigation links",
                "color": YELLOW
            },
            {
                "name": "Testing Suite",
                "desc": "Complete unit test coverage with\npytest for reliable development",
                "color": ORANGE
            }
        ]

        feature_cards = []
        for i, feature in enumerate(features):
            # Create feature card
            card = Rectangle(width=3.5, height=1.2, color=feature["color"], fill_opacity=0.1)
            card.move_to(
                LEFT * 3.5 + RIGHT * (i % 2) * 3.5 +
                DOWN * (i // 2) * 1.8 +
                UP * 2
            )

            name_text = Text(feature["name"], font_size=16, color=feature["color"])
            name_text.move_to(card.get_top() + DOWN * 0.3  )

            desc_text = Text(feature["desc"], font_size=12, color=WHITE, line_spacing=0.8)
            desc_text.move_to(card.get_center() + DOWN * 0.2)

            feature_cards.extend([card, name_text, desc_text])

        self.play(Write(title))
        for card, name, desc in zip(feature_cards[::3], feature_cards[1::3], feature_cards[2::3]):
            self.play(Create(card), Write(name), Write(desc))
            self.wait(0.5)

        self.wait(4)

        # Clear scene
        all_elements = [title] + feature_cards
        self.play(*[FadeOut(elem) for elem in all_elements])