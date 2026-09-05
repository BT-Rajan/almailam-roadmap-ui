export default {
  unknownProject: 'مشروع غير معروف',

  status: {
    draft: 'مسودة',
    underReview: 'قيد المراجعة',
    approved: 'معتمد',
    rejected: 'مرفوض',
  },

  type: {
    drawing: 'مخطط',
    report: 'تقرير',
    contract: 'عقد',
    quotation: 'عرض سعر',
    municipalityForm: 'نموذج بلدية',
    calculationSheet: 'ورقة حسابات',
    governmentAgreement: 'اتفاقية حكومية',
  },

  metadataPanel: {
    title: 'البيانات الوصفية',
    project: 'المشروع',
    category: 'الفئة',
    revision: 'المراجعة',
    uploadedBy: 'رفعه',
    uploadDate: 'تاريخ الرفع',
    fileSize: 'حجم الملف',
  },

  versionHistory: {
    title: 'سجل الإصدارات',
    emptyTitle: 'لا توجد إصدارات سابقة',
    current: 'الحالي',
    downloadThisVersion: 'تنزيل هذا الإصدار',
  },

  pdfViewer: {
    pageOf: 'صفحة {current} من {total}',
    zoomOut: 'تصغير',
    zoomIn: 'تكبير',
    previewPage: 'معاينة الصفحة {page}',
  },

  fileUploader: {
    clickToUpload: 'انقر للرفع أو اسحب وأفلت',
    defaultHint: 'ملفات PDF أو Word أو Excel أو DWG أو صور',
    removeFile: 'إزالة الملف',
  },

  card: {
    viewDocument: 'عرض المستند',
    downloadDocument: 'تنزيل المستند',
    editDocument: 'تعديل المستند',
    deleteDocument: 'حذف المستند',
    removeDocument: 'إزالة المستند',
  },

  documentsPage: {
    pageTitle: 'أرشيف المستندات',
    pageSubtitle: 'تصفح المستندات وإدارتها لجميع المشاريع في مكان واحد.',
    uploadDocument: 'رفع مستند',
    allCategories: 'جميع الفئات',
    gridView: 'عرض الشبكة',
    tableView: 'عرض الجدول',
    noDocumentsFound: 'لا توجد مستندات',
    noDocumentsFoundDescription: 'حاول تعديل البحث أو عوامل التصفية، أو ارفع مستندًا جديدًا.',
    columnTitle: 'عنوان المستند',
    columnCategory: 'الفئة',
    columnProject: 'المشروع',
    columnRevision: 'المراجعة',
    columnUploadedBy: 'رفعه',
    columnUploadDate: 'تاريخ الرفع',
    columnStatus: 'الحالة',
  },

  viewerPage: {
    documentViewer: 'عارض المستندات',
    download: 'تنزيل',
    status: 'الحالة',
    addVersion: 'إضافة إصدار',
    deleteDocument: 'حذف المستند',
    comments: 'التعليقات',
    noCommentsYet: 'لا توجد تعليقات بعد',
    noCommentsYetDescription: 'ستظهر سلاسل التعليقات لهذا المستند هنا.',
    documentNotFound: 'المستند غير موجود',
    documentNotFoundDescription: 'ربما تمت إزالة هذا المستند أو أن الرابط غير صحيح.',
  },

  addLinkDialog: {
    title: 'إضافة مستند',
    category: 'الفئة',
    categoryPlaceholder: 'اختر الفئة',
    categoryProperty: 'مستندات الملكية',
    categoryGovernment: 'مستندات حكومية',
    categoryOthers: 'أخرى',
    categoryProjectClosure: 'إغلاق المشروع',
    documentName: 'اسم المستند',
    documentNamePlaceholder: 'مثال: سند الملكية',
    documentPathLink: 'مسار المستند / الرابط',
    documentPathLinkPlaceholder: 'مثال: https://drive.example.com/... أو \\\\server\\share\\file.pdf',
    addDocument: 'إضافة مستند',
  },

  addVersionDialog: {
    title: 'إضافة إصدار جديد',
    notes: 'ملاحظات',
    notesPlaceholder: 'ما الذي تغير في هذه المراجعة؟',
    uploadNewVersion: 'رفع إصدار جديد',
  },

  designDocumentDialog: {
    editTitle: 'تعديل المستند',
    addTitle: 'إضافة مستند',
    document: 'المستند',
    documentPlaceholder: 'مثال: مخطط إنشائي R1',
    date: 'التاريخ',
    link: 'الرابط',
  },

  statusDialog: {
    title: 'تغيير حالة المستند',
    newStatus: 'الحالة الجديدة',
    reason: 'السبب',
    reasonRequiredHint: 'مطلوب عند الرفض',
  },

  uploadDialog: {
    title: 'رفع مستند',
    documentTitle: 'عنوان المستند',
    documentTitlePlaceholder: 'مثال: مخطط إنشائي',
    project: 'المشروع',
    projectPlaceholder: 'اختر المشروع',
    documentType: 'نوع المستند',
    documentTypePlaceholder: 'اختر النوع',
    typeDrawing: 'مخطط',
    typeReport: 'تقرير',
    typeContract: 'عقد',
    typeQuotation: 'عرض سعر',
    typeMunicipalityForm: 'نموذج بلدية',
    typeCalculationSheet: 'ورقة حسابات',
    typeGovernmentAgreement: 'اتفاقية حكومية',
    uploadDocument: 'رفع المستند',
  },
}
