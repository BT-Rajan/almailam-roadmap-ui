"""The reference-letter layout shared by the government-form PDF and DOCX.

letter_blocks decides each line's role (date, subject, field, body, ...);
both renderers depend on those roles, so they're checked here directly.
"""

import io
import unittest

from docx import Document

from app.services import pdf_render


class LetterBlocksTest(unittest.TestCase):
    def test_roles_follow_the_reference_letter(self):
        body = (
            "التاريخ : 2026/11/21\n\n"
            "السادة / بلدية الكويت – إدارة التراخيص الهندسية المحترمين\n\n"
            "تحية طيبة وبعد،،،\n\n"
            "الموضوع: تعهد تصميم إنشائي\n\n"
            "المالك/ محمد علي (طرف ثاني)\n"
            "منطقة / السالمية\n"
            "قطعة / 12\n\n"
            "حيث تم التصميم على مسؤولية المكتب، ونخلي طرف البلدية من أدنى مسؤولية.\n"
            "والتنفيذ تحت اشراف مكتب هندسي.\n\n"
            "وتفضلوا بقبول فائق الإحترام ،،\n\n"
            "طرف أول: مكتب عبد الهادي                    طرف ثاني: محمد علي"
        )
        roles = [role for role, _ in pdf_render.letter_blocks(body)]
        self.assertEqual(
            roles,
            ["date", "addressee", "salutation", "subject", "field", "field", "field", "body", "closing", "signature"],
        )

    def test_consecutive_body_lines_stay_one_block(self):
        blocks = pdf_render.letter_blocks("first line\nsecond line")
        self.assertEqual(blocks, [("body", "first line\nsecond line")])

    def test_filled_field_values_keep_their_field_role(self):
        # Field detection runs on rendered text, so a long value must not turn a field into body text.
        blocks = pdf_render.letter_blocks("منطقة / السالمية الجديدة الشمالية الكبيرة")
        self.assertEqual(blocks[0][0], "field")


class LetterRenderTest(unittest.TestCase):
    def test_docx_is_right_to_left_with_letter_roles(self):
        body = "التاريخ : 2026/11/21\n\nالموضوع: تعهد تصميم إنشائي\n\nنص الفقرة الأولى."
        docx_bytes = pdf_render.render_agreement_docx("Structural Design Undertaking", body)
        document = Document(io.BytesIO(docx_bytes))

        texts = [paragraph.text for paragraph in document.paragraphs]
        self.assertIn("الموضوع: تعهد تصميم إنشائي", texts)
        # Title is not repeated above a letter that has its own subject line.
        self.assertNotIn("Structural Design Undertaking", texts)

        subject = next(p for p in document.paragraphs if p.text.startswith("الموضوع"))
        self.assertTrue(subject.runs[0].underline)
        self.assertTrue(subject._p.pPr.xml.count("w:bidi"))

    def test_title_is_used_when_the_body_has_no_subject(self):
        docx_bytes = pdf_render.render_agreement_docx("Supervision Agreement", "Plain body text.")
        texts = [paragraph.text for paragraph in Document(io.BytesIO(docx_bytes)).paragraphs]
        self.assertEqual(texts[0], "Supervision Agreement")

    def test_pdf_is_produced(self):
        pdf_bytes = pdf_render.render_agreement_pdf("Title", "التاريخ : 2026/11/21\n\nنص.")
        self.assertTrue(pdf_bytes.startswith(b"%PDF"))


if __name__ == "__main__":
    unittest.main()
