package com.nad.riyadalsalheen.ui.screens

import androidx.compose.foundation.BorderStroke
import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.material3.TopAppBarDefaults
import androidx.compose.runtime.Composable
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.graphics.graphicsLayer
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.vectorResource
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import android.content.Intent
import android.net.Uri
import androidx.compose.foundation.clickable
import androidx.compose.ui.platform.LocalContext
import androidx.compose.ui.res.stringResource
import com.nad.riyadalsalheen.R

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun AboutScreen(
    onBackPressed: () -> Unit
) {

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    Text(
                        text = "حول التطبيق",
                        style = MaterialTheme.typography.titleLarge,
                        fontWeight = FontWeight.Bold
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBackPressed) {
                        Icon(
                            imageVector = ImageVector.vectorResource(R.drawable.ic_arrow_back_24),
                            contentDescription = "رجوع"
                        )
                    }
                },
                colors = TopAppBarDefaults.topAppBarColors(
                    containerColor = MaterialTheme.colorScheme.surface
                )
            )
        }
    ) { paddingValues ->
        LazyColumn(
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
                .padding(horizontal = 20.dp),
            verticalArrangement = Arrangement.spacedBy(16.dp)
        ) {
            item { Spacer(modifier = Modifier.height(8.dp)) }

            // App Info Card
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.primaryContainer.copy(alpha = 0.3f)
                    ),
                    shape = RoundedCornerShape(16.dp)
                ) {
                    Icon(
                        imageVector = ImageVector.vectorResource(R.drawable.ic_launcher_foreground),
                        contentDescription = null,
                        modifier = Modifier
                            .fillMaxWidth()
                            .height(128.dp)
                            .graphicsLayer(
                                scaleX = 1.5f, // Zoom in horizontally
                                scaleY = 1.5f, // Zoom in vertically
                                clip = true    // Clip to the original bounds
                            ),
                        tint = MaterialTheme.colorScheme.primary
                    )
                }
            }

            // About the Book
            item {
                AboutSection(
                    title = "عن الكتاب",
                    content = "كتاب رياض الصالحين من كلام سيد المرسلين هو كتاب حديث نبوي جليل من تأليف الإمام النووي، " +
                            "جمع فيه الأحاديث الصحيحة المتعلقة بأمور الآخرة وأعمال القلوب والجوارح والأخلاق والآداب والتربية الإسلامية. " +
                            "يعد هذا الكتاب من أشهر كتب الحديث وأكثرها انتشاراً وقراءة في العالم الإسلامي. " +
                            "ويعتمد التطبيق في الشرح على كتاب \"نزهة المتقين شرح رياض الصالحين\"."
                )
            }

            // About the Author
            item {
                AboutSection(
                    title = "عن المؤلف",
                    content = "الإمام محيي الدين يحيى بن شرف النووي (631-676 هـ) من كبار علماء الحديث والفقه الشافعي، " +
                            "له مؤلفات عديدة منها شرح صحيح مسلم والمجموع شرح المهذب والأذكار. اشتهر بورعه وزهده وتفانيه في طلب العلم."
                )
            }

            // About the App
            item {
                AboutSection(
                    title = "عن التطبيق",
                    content = "تطبيق رياض الصالحين يوفر تجربة قراءة مريحة وسهلة لكتاب رياض الصالحين. " +
                            "يتضمن التطبيق:\n\n" +
                            "• النص الكامل للأحاديث مع الشرح\n" +
                            "• تنظيم الأحاديث حسب الأبواب والكتب\n" +
                            "• إمكانية البحث في الأحاديث\n" +
                            "• حفظ العلامات المرجعية\n" +
                            "• التنقل السلس بين الأحاديث\n" +
                            "• مشاركة الاحاديث\n" +
                            "• تخصيص حجم الخط\n" +
                            "• الوضع الليلي\n\n" +
                            "تم بناء قاعدة البيانات الخاصة بهذا التطبيق بالاعتماد على قاعدة بيانات تطبيق آخر من تطوير \"مجموعة زاد\"."
                )
            }

            // Features Card
            item {
                Card(
                    modifier = Modifier.fillMaxWidth(),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.surfaceVariant.copy(alpha = 0.5f)
                    ),
                    shape = RoundedCornerShape(12.dp)
                ) {
                    Column(
                        modifier = Modifier.padding(16.dp)
                    ) {
                        FeatureItem(
                            icon = R.drawable.ic_bookmark_24,
                            text = "احفظ أحاديثك المفضلة"
                        )

                        Spacer(modifier = Modifier.height(12.dp))

                        FeatureItem(
                            icon = R.drawable.ic_share_24,
                            text = "شارك الاحاديث (ضغطة طويلة)"
                        )

                        Spacer(modifier = Modifier.height(12.dp))

                        FeatureItem(
                            icon = R.drawable.ic_search_24,
                            text = "ابحث في جميع الأحاديث"
                        )

                        Spacer(modifier = Modifier.height(12.dp))

                        FeatureItem(
                            icon = R.drawable.ic_text_fields_24,
                            text = "تحكم في حجم الخط"
                        )

                        Spacer(modifier = Modifier.height(12.dp))

                        FeatureItem(
                            icon = R.drawable.ic_dark_mode_24,
                            text = "وضع القراءة الليلي"
                        )
                    }
                }
            }

            // Contact Developer Section
            item {
                val context = LocalContext.current
                val email = "1992please@gmail.com"
                val githubUrl = "https://github.com/1992please/riyad-alsalheen"
                val subject = stringResource(R.string.email_subject)

                Column(
                    modifier = Modifier.fillMaxWidth()
                ) {
                    Text(
                        text = stringResource(R.string.contact_developer),
                        style = MaterialTheme.typography.titleMedium,
                        fontWeight = FontWeight.Bold,
                        color = MaterialTheme.colorScheme.primary,
                        modifier = Modifier.padding(bottom = 8.dp)
                    )

                    Card(
                        modifier = Modifier.fillMaxWidth(),
                        colors = CardDefaults.cardColors(
                            containerColor = MaterialTheme.colorScheme.surface
                        ),
                        shape = RoundedCornerShape(12.dp),
                        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
                    ) {
                        Column {
                            ContactItem(
                                icon = R.drawable.ic_info_24,
                                text = stringResource(R.string.send_email),
                                onClick = {
                                    val intent = Intent(Intent.ACTION_SENDTO).apply {
                                        data = Uri.parse("mailto:$email")
                                        putExtra(Intent.EXTRA_SUBJECT, subject)
                                    }
                                    context.startActivity(Intent.createChooser(intent, "إرسال بريد إلكتروني"))
                                }
                            )

                            ContactItem(
                                icon = R.drawable.ic_menu_book_24,
                                text = stringResource(R.string.developer_github),
                                onClick = {
                                    val intent = Intent(Intent.ACTION_VIEW, Uri.parse(githubUrl))
                                    context.startActivity(intent)
                                }
                            )
                        }
                    }
                }
            }

            // Footer
            item {
                Column(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(vertical = 16.dp),
                    horizontalAlignment = Alignment.CenterHorizontally
                ) {
                    Text(
                        text = "نسأل الله أن ينفع بهذا العمل",
                        style = MaterialTheme.typography.bodyMedium,
                        fontWeight = FontWeight.SemiBold,
                        color = MaterialTheme.colorScheme.onSurfaceVariant,
                        textAlign = TextAlign.Center
                    )

                    Spacer(modifier = Modifier.height(8.dp))

                    Text(
                        text = "اللهم علمنا ما ينفعنا وانفعنا بما علمتنا",
                        style = MaterialTheme.typography.bodySmall,
                        fontWeight = FontWeight.Normal,
                        color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                        textAlign = TextAlign.Center
                    )
                }
            }

            item { Spacer(modifier = Modifier.height(16.dp)) }
        }
    }
}

@Composable
private fun AboutSection(
    title: String,
    content: String
) {
    Card(
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        shape = RoundedCornerShape(12.dp),
        border = BorderStroke(1.dp, MaterialTheme.colorScheme.outlineVariant)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Text(
                text = title,
                style = MaterialTheme.typography.titleMedium,
                fontWeight = FontWeight.Bold,
                color = MaterialTheme.colorScheme.primary
            )

            Spacer(modifier = Modifier.height(8.dp))

            Text(
                text = content,
                style = MaterialTheme.typography.bodyMedium,
                fontWeight = FontWeight.Normal,
                color = MaterialTheme.colorScheme.onSurface,
                lineHeight = 24.sp
            )
        }
    }
}

@Composable
private fun FeatureItem(
    icon: Int,
    text: String
) {
    Row(
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = ImageVector.vectorResource(icon),
            contentDescription = null,
            modifier = Modifier.size(20.dp),
            tint = MaterialTheme.colorScheme.primary
        )

        Spacer(modifier = Modifier.width(12.dp))

        Text(
            text = text,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.SemiBold,
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}

@Composable
private fun ContactItem(
    icon: Int,
    text: String,
    onClick: () -> Unit
) {
    Row(
        modifier = Modifier
            .fillMaxWidth()
            .clickable(onClick = onClick)
            .padding(16.dp),
        verticalAlignment = Alignment.CenterVertically
    ) {
        Icon(
            imageVector = ImageVector.vectorResource(icon),
            contentDescription = null,
            modifier = Modifier.size(24.dp),
            tint = MaterialTheme.colorScheme.primary
        )

        Spacer(modifier = Modifier.width(16.dp))

        Text(
            text = text,
            style = MaterialTheme.typography.bodyMedium,
            fontWeight = FontWeight.SemiBold,
            color = MaterialTheme.colorScheme.onSurface
        )
    }
}
