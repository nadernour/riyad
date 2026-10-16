package com.nad.riyadalsalheen.ui.screens

import androidx.compose.foundation.layout.Arrangement
import androidx.compose.foundation.layout.Box
import androidx.compose.foundation.layout.Column
import androidx.compose.foundation.layout.PaddingValues
import androidx.compose.foundation.layout.Row
import androidx.compose.foundation.layout.Spacer
import androidx.compose.foundation.layout.fillMaxSize
import androidx.compose.foundation.layout.fillMaxWidth
import androidx.compose.foundation.layout.height
import androidx.compose.foundation.layout.padding
import androidx.compose.foundation.layout.size
import androidx.compose.foundation.layout.width
import androidx.compose.foundation.lazy.LazyColumn
import androidx.compose.foundation.lazy.items
import androidx.compose.foundation.shape.RoundedCornerShape
import androidx.compose.foundation.text.KeyboardOptions
import androidx.compose.material3.Card
import androidx.compose.material3.CardDefaults
import androidx.compose.material3.CircularProgressIndicator
import androidx.compose.material3.ExperimentalMaterial3Api
import androidx.compose.material3.Icon
import androidx.compose.material3.IconButton
import androidx.compose.material3.MaterialTheme
import androidx.compose.material3.OutlinedTextField
import androidx.compose.material3.OutlinedTextFieldDefaults
import androidx.compose.material3.Scaffold
import androidx.compose.material3.Text
import androidx.compose.material3.TopAppBar
import androidx.compose.runtime.Composable
import androidx.compose.runtime.LaunchedEffect
import androidx.compose.runtime.mutableStateOf
import androidx.compose.runtime.remember
import androidx.compose.ui.Alignment
import androidx.compose.ui.Modifier
import androidx.compose.ui.focus.FocusRequester
import androidx.compose.ui.focus.focusRequester
import androidx.compose.ui.graphics.vector.ImageVector
import androidx.compose.ui.res.vectorResource
import androidx.compose.ui.text.SpanStyle
import androidx.compose.ui.text.TextRange
import androidx.compose.ui.text.buildAnnotatedString
import androidx.compose.ui.text.font.FontWeight
import androidx.compose.ui.text.input.TextFieldValue
import androidx.compose.ui.text.intl.LocaleList
import androidx.compose.ui.text.style.TextAlign
import androidx.compose.ui.text.style.TextOverflow
import androidx.compose.ui.unit.dp
import androidx.compose.ui.unit.sp
import com.nad.riyadalsalheen.R
import com.nad.riyadalsalheen.model.Hadith
import com.nad.riyadalsalheen.ui.viewmodel.MIN_SEARCH_LENGTH
import com.nad.riyadalsalheen.ui.viewmodel.MainViewModel
import kotlinx.coroutines.delay

private const val SNIPPET_LENGTH = 200

@Composable
fun SearchScreen(
    viewModel: MainViewModel,
    onHadithSelected: (Int) -> Unit,
    onBackPressed: () -> Unit
) {

    SearchScreenContent(
        searchQuery = viewModel.searchQuery.value,
        searchResults = viewModel.searchResults.value,
        isSearching = viewModel.isSearching.value,
        onSearch = { query ->
            viewModel.searchHadiths(query)
        },
        onHadithSelected = onHadithSelected,
        onBackPressed = onBackPressed,
    )
}

@OptIn(ExperimentalMaterial3Api::class)
@Composable
fun SearchScreenContent(
    searchQuery: String,
    searchResults: List<Hadith> = emptyList(),
    isSearching: Boolean = false,
    onSearch: (String) -> Unit = {},
    onHadithSelected: (Int) -> Unit = {},
    onBackPressed: () -> Unit = {}
) {
    val focusRequester = remember { FocusRequester() }
    val textFieldValueState = remember {
        mutableStateOf(TextFieldValue(text = searchQuery, selection = TextRange(searchQuery.length)))
    }

    LaunchedEffect(Unit) {
        delay(100)
        focusRequester.requestFocus()
    }

    Scaffold(
        topBar = {
            TopAppBar(
                title = {
                    OutlinedTextField(
                        value = textFieldValueState.value,
                        keyboardOptions = KeyboardOptions(hintLocales = LocaleList("ar")),
                        onValueChange = { newTextFieldValueState ->
                            textFieldValueState.value = newTextFieldValueState
                            if(newTextFieldValueState.text != searchQuery) {
                                onSearch(newTextFieldValueState.text)
                            }
                        },
                        modifier = Modifier
                            .fillMaxWidth()
                            .focusRequester(focusRequester),
                        placeholder = {
                            Text(
                                text = "ابحث عن كلمة أو رقم الحديث...",
                                style = MaterialTheme.typography.bodyLarge,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        },
                        leadingIcon = {
                            Icon(
                                imageVector = ImageVector.vectorResource(R.drawable.ic_search_24),
                                contentDescription = "بحث",
                                tint = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                        },
                        trailingIcon = {
                            when {
                                isSearching -> {
                                    CircularProgressIndicator(
                                        modifier = Modifier.size(24.dp),
                                        strokeWidth = 2.dp
                                    )
                                }
                                searchQuery.isNotEmpty() -> {
                                    IconButton(
                                        onClick = {
                                            onSearch("")
                                        }
                                    ) {
                                        Icon(
                                            imageVector = ImageVector.vectorResource(R.drawable.ic_clear_24),
                                            contentDescription = "مسح"
                                        )
                                    }
                                }
                            }
                        },
                        singleLine = true,
                        shape = RoundedCornerShape(28.dp),
                        colors = OutlinedTextFieldDefaults.colors(
                            focusedBorderColor = MaterialTheme.colorScheme.primary,
                            unfocusedBorderColor = MaterialTheme.colorScheme.surfaceVariant
                        ),
                        textStyle = MaterialTheme.typography.bodyLarge
                    )
                },
                navigationIcon = {
                    IconButton(onClick = onBackPressed) {
                        Icon(
                            imageVector = ImageVector.vectorResource(R.drawable.ic_arrow_back_24),
                            contentDescription = "رجوع"
                        )
                    }
                }
            )
        }
    ) { paddingValues ->
        Column (
            modifier = Modifier
                .fillMaxSize()
                .padding(paddingValues)
        ) {
            if (searchQuery.isNotEmpty() && searchQuery.length < MIN_SEARCH_LENGTH) {
                Card(
                    modifier = Modifier
                        .fillMaxWidth()
                        .padding(start = 16.dp, end = 16.dp, top = 4.dp),
                    colors = CardDefaults.cardColors(
                        containerColor = MaterialTheme.colorScheme.tertiaryContainer.copy(alpha = 0.3f)
                    )
                ) {
                    Row(
                        modifier = Modifier.padding(12.dp),
                        verticalAlignment = Alignment.CenterVertically
                    ) {
                        Icon(
                            imageVector = ImageVector.vectorResource(R.drawable.ic_info_24),
                            contentDescription = null,
                            tint = MaterialTheme.colorScheme.tertiary,
                            modifier = Modifier.size(20.dp)
                        )
                        Spacer(modifier = Modifier.width(8.dp))
                        Text(
                            text = "اكتب ٣ أحرف على الأقل للبحث",
                            style = MaterialTheme.typography.bodyMedium,
                            color = MaterialTheme.colorScheme.onTertiaryContainer
                        )
                    }
                }
            }

            when {
                searchQuery.isEmpty() -> {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(32.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Icon(
                                imageVector = ImageVector.vectorResource(R.drawable.ic_search_24),
                                contentDescription = null,
                                modifier = Modifier.size(64.dp),
                                tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                text = "ابحث في رياض الصالحين",
                                style = MaterialTheme.typography.titleMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = "يمكنك البحث في نص الحديث أو الشرح",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f),
                                textAlign = TextAlign.Center
                            )
                        }
                    }
                }

                searchResults.isEmpty() && searchQuery.length >= MIN_SEARCH_LENGTH && !isSearching -> {
                    Box(
                        modifier = Modifier
                            .fillMaxSize()
                            .padding(32.dp),
                        contentAlignment = Alignment.Center
                    ) {
                        Column(horizontalAlignment = Alignment.CenterHorizontally) {
                            Icon(
                                imageVector = ImageVector.vectorResource(id = R.drawable.ic_search_off_24),
                                contentDescription = null,
                                modifier = Modifier.size(64.dp),
                                tint = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.5f)
                            )
                            Spacer(modifier = Modifier.height(16.dp))
                            Text(
                                text = "لم يتم العثور على نتائج",
                                style = MaterialTheme.typography.titleMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant
                            )
                            Spacer(modifier = Modifier.height(8.dp))
                            Text(
                                text = "جرب البحث بكلمات أخرى",
                                style = MaterialTheme.typography.bodyMedium,
                                color = MaterialTheme.colorScheme.onSurfaceVariant.copy(alpha = 0.7f)
                            )
                        }
                    }
                }

                else -> {
                    Column {
                        if (searchResults.isNotEmpty()) {
                            Card(
                                modifier = Modifier
                                    .fillMaxWidth()
                                    .padding(horizontal = 16.dp, vertical = 8.dp),
                                colors = CardDefaults.cardColors(
                                    containerColor = MaterialTheme.colorScheme.secondaryContainer
                                )
                            ) {
                                Text(
                                    text = "عدد النتائج: ${searchResults.size}",
                                    modifier = Modifier.padding(12.dp),
                                    style = MaterialTheme.typography.bodyMedium,
                                    color = MaterialTheme.colorScheme.onSecondaryContainer
                                )
                            }
                        }

                        LazyColumn(
                            modifier = Modifier.fillMaxSize(),
                            contentPadding = PaddingValues(16.dp),
                            verticalArrangement = Arrangement.spacedBy(8.dp)
                        ) {
                            items(searchResults) { hadith ->
                                SearchResultItem(
                                    hadith = hadith,
                                    searchQuery = searchQuery,
                                    onClick = { onHadithSelected(hadith.id) }
                                )
                            }
                        }
                    }
                }
            }
        }
    }
}

@Composable
fun SearchResultItem(
    hadith: Hadith,
    searchQuery: String,
    onClick: () -> Unit
) {
    Card(
        onClick = onClick,
        modifier = Modifier.fillMaxWidth(),
        colors = CardDefaults.cardColors(
            containerColor = MaterialTheme.colorScheme.surface
        ),
        elevation = CardDefaults.cardElevation(defaultElevation = 2.dp)
    ) {
        Column(
            modifier = Modifier.padding(16.dp)
        ) {
            Row(
                modifier = Modifier.fillMaxWidth(),
                horizontalArrangement = Arrangement.SpaceBetween,
                verticalAlignment = Alignment.CenterVertically
            ) {
                Text(
                    text = "الحديث ${hadith.id}",
                    style = MaterialTheme.typography.labelSmall,
                    color = MaterialTheme.colorScheme.primary
                )
                if (hadith.title.isNotBlank()) {
                    Text(
                        text = hadith.title,
                        style = MaterialTheme.typography.titleSmall,
                        fontWeight = FontWeight.SemiBold,
                        modifier = Modifier.weight(1f),
                        textAlign = TextAlign.End,
                        maxLines = 1,
                        overflow = TextOverflow.Ellipsis
                    )
                }
            }

            Spacer(modifier = Modifier.height(8.dp))

            val isSearchingById = searchQuery.toIntOrNull() == hadith.id
            val fullText = hadith.matn_normal
            val indexOfSearch = if (isSearchingById) -1 else fullText.indexOf(searchQuery)
            val snippet = if (fullText.length > SNIPPET_LENGTH) {
                if(indexOfSearch == -1) fullText.substring(0, SNIPPET_LENGTH) + "..."
                else {
                    val startIndex = (indexOfSearch - SNIPPET_LENGTH / 2).coerceAtLeast(0)
                    val endIndex = (indexOfSearch + SNIPPET_LENGTH / 2).coerceIn(0,fullText.length)
                    val startEllipses = if(startIndex == 0) "" else "..."
                    val endEllipses = if(endIndex == fullText.length) "" else "..."
                    startEllipses + fullText.substring(startIndex, endIndex) + endEllipses
                }
            } else {
                fullText
            }

            val annotatedText = buildAnnotatedString {
                append(snippet)
                if (searchQuery.isNotBlank() && !isSearchingById) {
                    val startIndex = snippet.indexOf(searchQuery, ignoreCase = true)
                    if (startIndex != -1) {
                        val endIndex = startIndex + searchQuery.length
                        addStyle(
                            style = SpanStyle(
                                color = MaterialTheme.colorScheme.onSurface,
                                background = MaterialTheme.colorScheme.primaryContainer,
                                fontWeight = FontWeight.Bold
                            ),
                            start = startIndex,
                            end = endIndex
                        )
                    }
                }
            }

            Text(
                text = annotatedText,
                style = MaterialTheme.typography.bodyMedium,
                lineHeight = 22.sp,
                maxLines = 3,
                overflow = TextOverflow.Ellipsis,
                color = MaterialTheme.colorScheme.onSurfaceVariant
            )
        }
    }
}